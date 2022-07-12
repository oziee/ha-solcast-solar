"""Solcast API."""
from __future__ import annotations

import json
import logging
import traceback
from dataclasses import dataclass
from datetime import datetime as dt
from datetime import timedelta, timezone
from operator import itemgetter
from os.path import exists as file_exists
from typing import Any, cast

from homeassistant.core import HomeAssistant
from aiohttp import ClientConnectionError, ClientSession
import asyncio
import async_timeout
from aiohttp.client_reqrep import ClientResponse
from isodate import parse_datetime

_LOGGER = logging.getLogger(__name__)

class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, dt):
            return o.isoformat()

class JSONDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(
            self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        ret = {}
        for key, value in obj.items():
            if key in {'period_end'}:
                ret[key] = dt.fromisoformat(value) 
            else:
                ret[key] = value
        return ret

@dataclass
class ConnectionOptions:
    """Solcast API options for connection."""

    api_key: str 
    host: str


class SolcastApi:
    """Solcast API rooftop."""

    def __init__(
        self,
        hass: HomeAssistant,
        aiohttp_session: ClientSession,
        options: ConnectionOptions,
    ):
        """Device init."""
        self.hass = hass
        self.aiohttp_session = aiohttp_session
        self.options = options
        self._sites = []
        self._data = dict({'forecasts':[], 'energy': {}, 'api_used':0, 'last_updated': dt.now(timezone.utc).replace(year=2000,month=1,day=1).isoformat()})
        self._api_used = 0
        self._filename = self.hass.config.path('solcast.json')

    async def sites_data(self):
        """Request data via the Solcast API."""
        
        try:
            sp = self.options.api_key.split(",")
            for spl in sp:
                #params = {"format": "json", "api_key": self.options.api_key}
                params = {"format": "json", "api_key": spl.strip()}
                async with async_timeout.timeout(10):
                    resp: ClientResponse = await self.aiohttp_session.get(
                        url=f"{self.options.host}/rooftop_sites", params=params, ssl=False
                    )
    
                    resp_json = await resp.json(content_type=None)
                    status = resp.status

                if status == 200:
                    #self._api_used = self._api_used + 1
                    d = cast(dict, resp_json)
                    for i in d['sites']:
                        i['apikey'] = spl.strip()

                    self._sites = self._sites + d['sites']
                else:
                    _LOGGER.error(
                        f"Solcast Error {status} - Gathering rooftop sites data."
                    )
                    raise Exception(f"HTTP error: Solcast Error gathering rooftop sites data.")
        except ConnectionRefusedError as err:
            _LOGGER.error("Solcast Error.. %s",err)
        except ClientConnectionError as e:
            _LOGGER.error('Solcast Connection Error', str(e))
        except asyncio.TimeoutError:
            _LOGGER.error("Solcast Connection Error - Timed out connection to solcast server")
        except Exception as e:
            _LOGGER.error("Solcast http_data error: %s", traceback.format_exc())

    async def load_saved_data(self):

        if len(self._sites) > 0:
            if file_exists(self._filename):
                with open(self._filename) as data_file:
                    self._data = json.load(data_file, cls=JSONDecoder)
                if self._data and "api_used" in self._data:
                    self._api_used = self._data["api_used"]
            else:
                #no file to load
                await self.http_data(True)

    async def force_api_poll(self, *args):
        if args:
            await self.http_data(args[0])
        else:
            await self.http_data()

    def get_api_used_count(self) -> int:
        """Return API polling count for this UTC 24hr period"""
        try:
            sites = len(self._sites)
            polls = self._api_used
            if sites==1:
                #only one site
                return 50 - int(self._api_used)
            elif sites%2 == 0:
                #even number of sites
                return 50 - int((polls / sites) * 2)
            else:
                #odd number of sites.. max 2 sites per api_key.. so max polls for 2 sites
                return 50 - int((polls - (polls / sites)))

        except Exception:
            return -1

    def get_last_updated_datetime(self) -> dt:
        """Return date time with the data was last updated"""
        try:
            return dt.fromisoformat(self._data["last_updated"])
        except Exception:
            return dt.now(timezone.utc).replace(year=2000,month=1,day=1).isoformat()

    async def reset_api_counter(self):
        self._api_used = 0

    def get_rooftop_site_total_today(self, rooftopid = "") -> float:
        """Return a rooftop sites total kw for today"""
        #g = [d for d in self._sites if d['resource_id'] == rooftopid]   
        try:
            return self._data["siteinfo"][rooftopid]['tally']
        except Exception:
            return 0

    def get_rooftop_site_extra_data(self, rooftopid = "") -> float:
        """Return a rooftop sites total kw for today"""
        try:
            g = [d for d in self._sites if d['resource_id'] == rooftopid]   
            site = g[0]
            d = {}

            if "name" in site:
                d["name"] = site["name"]
            if "resource_id" in site:
                d["resource_id"] = site["resource_id"]
            if "capacity" in site:
                d["capacity"] = site["capacity"]
            if "capacity_dc" in site:
                d["capacity_dc"] = site["capacity_dc"]
            if "longitude" in site:
                d["longitude"] = site["longitude"]
            if "latitude" in site:
                d["latitude"] = site["latitude"]
            if "azimuth" in site:
                d["azimuth"] = site["azimuth"]
            if "tilt" in site:
                d["tilt"] = site["tilt"]
            if "install_date" in site:
                d["install_date"] = site["install_date"]
            if "loss_factor" in site:
                d["loss_factor"] = site["loss_factor"]

            return d
        except Exception:
            return {}

    def get_remaining_today(self):
        """Return Remaining Forecasts data for today"""
        try:
            da = dt.now().replace(minute=0, second=0, microsecond=0)
            h = da.hour
            da = da.date()
            g = [d for d in self._data["forecasts"] if d['period_end'].date() == da]
            tot = 0
            for p in g:
                if p["period_end"].hour >= h:
                    tot += p["pv_estimate"]
            
            return round(tot,2)
        except Exception:
            return 0
    
    def get_forecast_today(self) -> dict[str, Any]:
        """Return Solcast Forecasts data for today"""
        try:
            da = dt.now().replace(minute=0, second=0, microsecond=0).date()
            g = [d for d in self._data["forecasts"] if d['period_end'].date() == da]
            return {"forecast": g}
        except Exception:
            return {}

    def get_forecast_tomorrow(self) -> dict[str, Any]:
        """Return Solcast Forecasts data for tomorrow"""
        try:
            da = dt.now().replace(minute=0, second=0, microsecond=0).date() + timedelta(days=1)
            g = [d for d in self._data["forecasts"] if d['period_end'].date() == da]
            return {"forecast": g}
        except Exception:
            return {}

    def get_forecast_this_hour(self) -> int:
        try:
            da = dt.now().replace(minute=0, second=0, microsecond=0).astimezone()
            g = [d for d in self._data["forecasts"] if d['period_end'] == da]   
            return int(g[0]['pv_estimate'] * 1000)
        except Exception:
            return 0

    def get_forecast_next_hour(self) -> int:
        try:
            da = dt.now().replace(minute=0, second=0, microsecond=0).astimezone() + timedelta(hours=1)
            g = [d for d in self._data["forecasts"] if d['period_end'] == da]   
            return int(g[0]['pv_estimate'] * 1000)
        except Exception:
            return 0

    def get_total_kwh_forecast_today(self) -> float:
        """Return total kwh total for rooftop site today"""
        try:
            da = dt.now().replace(minute=0, second=0, microsecond=0).date()
            g = [d for d in self._data["forecasts"] if d['period_end'].date() == da]
            return round(sum(z['pv_estimate'] for z in g if z),2)
        except Exception:
            return 0

    def get_peak_w_today(self) -> int:
        """Return hour of max kw for rooftop site today"""
        try:
            da = dt.now().replace(minute=0, second=0, microsecond=0).date()
            g = [d for d in self._data["forecasts"] if d['period_end'].date() == da]
            m = max(z['pv_estimate'] for z in g if z) 
            return int(m * 1000)
        except Exception:
            return 0

    def get_peak_w_time_today(self) -> dt:
        """Return hour of max kw for rooftop site today"""
        try:
            da = dt.now().replace(minute=0, second=0, microsecond=0).date()
            g = [d for d in self._data["forecasts"] if d['period_end'].date() == da]
            m = max(z['pv_estimate'] for z in g if z) 

            for v in g:
                if v['pv_estimate'] == m:
                    return v['period_end']
                    #return p.isoformat()
            return None
        except Exception:
            return None

    def get_total_kwh_forecast_tomorrow(self) -> float:
        """Return total kwh total for rooftop site tomorrow"""
        try:
            da = dt.now().replace(minute=0, second=0, microsecond=0).date() + timedelta(days=1)
            g = [d for d in self._data["forecasts"] if d['period_end'].date() == da]
            return round(sum(z['pv_estimate'] for z in g if z),2)
        except Exception:
            return 0

    def get_peak_w_tomorrow(self) -> int:
        """Return hour of max kw for rooftop site tomorrow"""
        try:
            da = dt.now().replace(minute=0, second=0, microsecond=0).date() + timedelta(days=1)
            g = [d for d in self._data["forecasts"] if d['period_end'].date() == da]
            m = max(z['pv_estimate'] for z in g if z) 
            return int(m * 1000)
        except Exception:
            return 0

    def get_peak_w_time_tomorrow(self) -> dt:
        """Return hour of max kw for rooftop site tomorrow"""
        try:
            da = dt.now().replace(minute=0, second=0, microsecond=0).date() + timedelta(days=1)
            g = [d for d in self._data["forecasts"] if d['period_end'].date() == da]
            m = max(z['pv_estimate'] for z in g if z) 

            for v in g:
                if v['pv_estimate'] == m:
                    return v['period_end']
                    #  return p.isoformat() ??
            return None
        except Exception:
            return None
    
    def get_energy_data(self) -> dict[str, Any]:
        try:
            return self._data["energy"]
        except Exception as e:
            _LOGGER.error(f"Solcast - get_energy_data: {e}")
            return None

    async def http_data(self, dopast = False):
        """Request data via the Solcast API."""
        
        try:
            
            today = dt.now().date()
            lastday = dt.now().date() + timedelta(days=7)

            _olddata = self._data

            #if dopast:
            self._data = []

            _s = {}

            _LOGGER.debug(f"Solcast polling for data")
            _LOGGER.debug(f"Solcast including past actual data? - {dopast}")

            for site in self._sites:
                _LOGGER.debug(f"Solcast api polling for rooftop {site['resource_id']}")
                # _LOGGER.debug(f" getting site: {site['resource_id']}")
                _data = []

                ae = None
                if dopast:
                    ae = await self.fetch_data("estimated_actuals", 28, site=site['resource_id'],  apikey=site['apikey'])
                    if not type(ae) is dict:
                        self._data = _olddata
                        return

                    for x in ae['estimated_actuals']:
                        z = parse_datetime(x['period_end']).astimezone() - timedelta(minutes=30)
                        if z.date() == today:
                            _data.append({"period_end": z,"pv_estimate": x["pv_estimate"]*0.5})

                    _data = sorted(_data, key=itemgetter("period_end"))
                    #_s.update({site['resource_id']:{'estimated_actuals': _data}})

                af = await self.fetch_data("forecasts", 168, site=site['resource_id'], apikey=site['apikey'])
                if not type(af) is dict:
                    self._data = _olddata
                    return

                _data2 = []
                for x in af['forecasts']:
                    z = parse_datetime(x['period_end']).astimezone() - timedelta(minutes=30)
                    if z.date() < lastday:
                        _data2.append({"period_end": z,"pv_estimate": x["pv_estimate"]*0.5})

                # _data2 = sorted(_data2, key=itemgetter("period_end"))
                # _s.update({site['resource_id']:{'forecasts': _data2}})
                
                if dopast:
                    _data = _data + _data2
                else:
                    #_LOGGER.debug("not doing past data so fill ion the blanks")
                    _data = _olddata['siteinfo'][site['resource_id']]['forecasts']
                    for item in _data2:
                        found_data = [d for d in _data if d['period_end'] == item['period_end']]
                        if len(found_data) > 0:
                            #_LOGGER.warn(f"found this to update {found_data[0]}")
                            found_data[0].update({"period_end": item['period_end'],"pv_estimate": item['pv_estimate']})
                        else:
                            #_LOGGER.warn(f"did not found update so adding to list")
                            _data.append({"period_end": item['period_end'],"pv_estimate": item['pv_estimate']})

                _data = sorted(_data, key=itemgetter("period_end"))
                _s.update({site['resource_id']:{'forecasts': _data}})

                # _LOGGER.debug("OK up to here now.. should be midnight today")
                # _LOGGER.debug(_data[0])

                for n in range(len(_data)-1):
                    _sec = _data[n+1]["period_end"] - _data[n]["period_end"]
                    if _sec.seconds > 1800:  #more than 30min then we are missing data
                        #_LOGGER.warn(f"Solcast missing forecast interval item from {_data[n]['period_end']} to {_data[n+1]['period_end']}")
                        findme = _data[n]["period_end"] + timedelta(minutes=30)
                        if site['resource_id'] in _olddata:
                            if 'forecasts' in _olddata[site['resource_id']] :
                                
                                inset_data = [d for d in _olddata[site['resource_id']]["forecasts"] if d['period_end'] == findme.isoformat()]
                                if len(inset_data) > 0:
                                    z = parse_datetime(inset_data[0]['period_end']).astimezone() 
                                    #_LOGGER.debug("adding missing solcast item {inset_data}")
                                    _data.append({"period_end": z,"pv_estimate": inset_data[0]["pv_estimate"]})
                                else:
                                    #_LOGGER.debug("IS old data to fill in the missing data but didnt find any match so adding empty item as 0 value")
                                    _data.append({"period_end": findme.astimezone(),"pv_estimate": 0})
                        else:
                            #_LOGGER.debug("No old data to fill in the missing data so adding empty item as 0 value")
                            _data.append({"period_end": findme.astimezone(),"pv_estimate": 0})

                _data = sorted(_data, key=itemgetter("period_end"))

                if not (len(_data) % 2) == 0:
                    del _data[-1]

                tally_today = 0
                for x in _data:
                    if x['period_end'].date() == today:
                        tally_today += x["pv_estimate"]

                _s[site['resource_id']]['tally'] = round(tally_today,2)

                # _LOGGER.debug("next data check.. should be midnight today")
                # _LOGGER.debug(_data[0])

                _d = []
                it = iter(_data)
                for x in it:
                    a = x
                    b = next(it)
                    # if not a['period_end'].hour == b['period_end'].hour:
                    #     #_LOGGER.error(f"not same hour for {a} and {b}")
                    #     _LOGGER.warn(f"solcast - api error.. dam it! still missing data from solcast api between hours {a} and {b}")
                    if a['period_end'].minute == 0:
                        _d.append({"period_end": a['period_end'],"pv_estimate": (a["pv_estimate"] + b["pv_estimate"])})
                    else:
                        #_LOGGER.warn("hmm this should not have data at the 30min mark.. should be on the hour values")
                        _t = a['period_end'].replace(minute=0)
                        _d.append({"period_end": _t,"pv_estimate": (a["pv_estimate"] + b["pv_estimate"])})


                if len(self._data) == 0:
                    self._data = _d
                else:
                    for number in range(len(self._data)):
                        p = self._data[number]
                        p["pv_estimate"] = float(p["pv_estimate"]) + float(_d[number]["pv_estimate"])

            if self._data == []:
                self._data = _olddata
                self._data['api_used'] = self._api_used
            else:
                #self._data = sorted(self._data, key=itemgetter("period_end"))
                self._data = dict({"forecasts": self._data})

                self._data["energy"] = {"wh_hours": self.makeenergydict()}

                self._data["siteinfo"] = _s

                self._data["last_updated"] = dt.now(timezone.utc).replace(second=0 ,microsecond=0).isoformat()
                self._data['api_used'] = self._api_used

            with open(self._filename, 'w') as f:
                json.dump(self._data, f, ensure_ascii=False, cls=DateTimeEncoder)


        except Exception as e:
            _LOGGER.error("Solcast http_data error: %s", traceback.format_exc())

    async def fetch_data(self, path= "error", hours=50, site="", apikey="") -> dict[str, Any]:
        """fetch data via the Solcast API."""
        
        try:
            params = {"format": "json", "api_key": apikey, "hours": hours}
            
            async with async_timeout.timeout(20):
                resp: ClientResponse = await self.aiohttp_session.get(
                    url=f"{self.options.host}/rooftop_sites/{site}/{path}", params=params, ssl=False
                )
    
                resp_json = await resp.json(content_type=None)
                status = resp.status

            if status == 429:
                _LOGGER.warning("Exceeded Solcast API allowed polling limit")
                self._api_used = 50
                #raise Exception(f"HTTP error: Exceeded Solcast API allowed polling limit")
            elif status == 400:
                _LOGGER.error(
                    "The rooftop site missing capacity, please specify capacity or provide historic data for tuning."
                )
                #raise Exception(f"HTTP error: The rooftop site missing capacity, please specify capacity or provide historic data for tuning.")
            elif status == 404:
                _LOGGER.error("The rooftop site cannot be found or is not accessible.")
                #raise Exception(f"HTTP error: The rooftop site cannot be found or is not accessible.")
            elif status == 200:
                self._api_used = self._api_used + 1
                d = cast(dict, resp_json)
                return d
                #await self.format_json_data(d)
        except ConnectionRefusedError as err:
            _LOGGER.error("Solcast Error.. %s",err)
        except ClientConnectionError as e:
            _LOGGER.error('Solcast Connection Error', str(e))
        except asyncio.TimeoutError:
            _LOGGER.error("Solcast Connection Error - Timed out connection to solcast server")
        except Exception as e:
            _LOGGER.error("Solcast fetch_data error: %s", traceback.format_exc())

        return None

    def makeenergydict(self) -> dict:
        wh_hours = {}

        lastv = -1
        lastk = -1
        for v in self._data["forecasts"]:
            d = v['period_end'].isoformat()
            if v['pv_estimate'] == 0.0:
                if lastv > 0.0:
                    wh_hours[d] = v['pv_estimate'] * 1000
                lastk = d
                lastv = v['pv_estimate']
            else:
                if lastv == 0.0:
                    #add the last one
                    wh_hours[lastk] = lastv * 1000

                wh_hours[d] = v['pv_estimate'] * 1000
                
                lastk = d
                lastv = v['pv_estimate']

        return wh_hours
