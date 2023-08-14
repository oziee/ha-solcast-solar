"""Solcast API."""
from __future__ import annotations

import asyncio
import copy
import json
import logging
import os
import traceback
from dataclasses import dataclass
from datetime import datetime as dt
from datetime import timedelta, timezone
from operator import itemgetter
from os.path import exists as file_exists
from typing import Any, cast

import async_timeout
from aiohttp import ClientConnectionError, ClientSession
from aiohttp.client_reqrep import ClientResponse
from isodate import parse_datetime

_JSON_VERSION = 3
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
            if key in {'period_start'}:
                ret[key] = dt.fromisoformat(value) 
            else:
                ret[key] = value
        return ret

@dataclass
class ConnectionOptions:
    """Solcast API options for connection."""

    api_key: str 
    host: str
    file_path: str
    tz: timezone


class SolcastApi:
    """Solcast API rooftop."""

    def __init__(
        self,
        aiohttp_session: ClientSession,
        options: ConnectionOptions,
        apiCacheEnabled: bool = False
    ):
        """Device init."""
        self.aiohttp_session = aiohttp_session
        self.options = options
        self.apiCacheEnabled = apiCacheEnabled
        self._sites = []
        self._data = dict({'siteinfo':{}, 'last_updated': dt.now(timezone.utc).replace(year=2000,month=1,day=1).isoformat()})
        self._api_used = 0
        self._api_limit = 0
        self._filename = options.file_path
        self._tz = options.tz
        #self._apiallusedup = False
        self._tzdataconverted = []
        self._dataenergy = {}
        self._dataforecasts = []
        self._detailedForecasts = []

    async def sites_data(self):
        """Request data via the Solcast API."""
        
        try:
            sp = self.options.api_key.split(",")
            for spl in sp:
                #params = {"format": "json", "api_key": self.options.api_key}
                params = {"format": "json", "api_key": spl.strip()}
                _LOGGER.debug(f"SOLCAST - trying to connect to - {self.options.host}/rooftop_sites?format=json&api_key=REDACTED")
                async with async_timeout.timeout(60):
                    apiCacheFileName = "sites.json"
                    if self.apiCacheEnabled and file_exists(apiCacheFileName):
                        status = 404
                        with open(apiCacheFileName) as f:
                            resp_json = json.load(f)
                            status = 200
                    else:
                        resp: ClientResponse = await self.aiohttp_session.get(
                            url=f"{self.options.host}/rooftop_sites", params=params, ssl=False
                        )
        
                        resp_json = await resp.json(content_type=None)
                        status = resp.status
                        if self.apiCacheEnabled:
                            with open(apiCacheFileName, 'w') as f:
                                json.dump(resp_json, f, ensure_ascii=False)
                            
                    _LOGGER.debug(f"SOLCAST - sites_data code http_session returned data type is {type(resp_json)}")
                    _LOGGER.debug(f"SOLCAST - sites_data code http_session returned status {status}")

                if status == 200:
                    d = cast(dict, resp_json)
                    _LOGGER.debug(f"SOLCAST - sites_data returned data: {d}")
                    for i in d['sites']:
                        i['apikey'] = spl.strip()

                    self._sites = self._sites + d['sites']
                else:
                    _LOGGER.warning(
                        f"SOLCAST - sites_data Solcast.com http status Error {status} - Gathering rooftop sites data."
                    )
                    raise Exception(f"SOLCAST - HTTP sites_data error: Solcast Error gathering rooftop sites data.")
        except json.decoder.JSONDecodeError:
            _LOGGER.error("SOLCAST - sites_data JSONDecodeError.. The data returned from Solcast is unknown, Solcast site could be having problems")
        except ConnectionRefusedError as err:
            _LOGGER.error("SOLCAST - sites_data Error.. %s",err)
        except ClientConnectionError as e:
            _LOGGER.error('SOLCAST - sites_data Connection Error', str(e))
        except asyncio.TimeoutError:
            _LOGGER.error("SOLCAST - sites_data Connection Error - Timed out connection to solcast server")
        except Exception as e:
            _LOGGER.error("SOLCAST - sites_data error: %s", traceback.format_exc())
            
    async def sites_usage(self):
        """Request api usage via the Solcast API."""
        
        try:
            sp = self.options.api_key.split(",")
 
            params = {"api_key": sp[0]}
            _LOGGER.debug(f"SOLCAST - getting usage data from solcast")
            async with async_timeout.timeout(60):
                resp: ClientResponse = await self.aiohttp_session.get(
                    url=f"https://api.solcast.com.au/json/reply/GetUserUsageAllowance", params=params, ssl=False
                )

                resp_json = await resp.json(content_type=None)
                status = resp.status

                        
                _LOGGER.debug(f"SOLCAST - sites_usage code http_session returned data type is {type(resp_json)}")
                _LOGGER.debug(f"SOLCAST - sites_usage code http_session returned status {status}")

            if status == 200:
                d = cast(dict, resp_json)
                _LOGGER.debug(f"SOLCAST - sites_usage returned data: {d}")
                if "daily_limit" in d:
                    self._api_limit = d["daily_limit"]
                    self._api_used = d["daily_limit_consumed"]
                else:
                    raise Exception(f"SOLCAST - HTTP sites_usage error: Solcast Error gathering usage data.")
            else:
                _LOGGER.warning(
                    f"SOLCAST - sites_usage Solcast.com http status Error {status} - Gathering usage data."
                )
                raise Exception(f"SOLCAST - HTTP sites_usage error: Solcast Error gathering usage data.")
        except json.decoder.JSONDecodeError:
            _LOGGER.error("SOLCAST - sites_usage JSONDecodeError.. The data returned from Solcast is unknown, Solcast site could be having problems")
        except ConnectionRefusedError as err:
            _LOGGER.error("SOLCAST - sites_usage Error.. %s",err)
        except ClientConnectionError as e:
            _LOGGER.error('SOLCAST - sites_usage Connection Error', str(e))
        except asyncio.TimeoutError:
            _LOGGER.error("SOLCAST - sites_usage Connection Error - Timed out connection to solcast server")
        except Exception as e:
            _LOGGER.error("SOLCAST - sites_usage error: %s", traceback.format_exc())

    async def load_saved_data(self):
        try:
            if len(self._sites) > 0:
                loadedData = False
                if file_exists(self._filename):
                    with open(self._filename) as data_file:
                        jsonData = json.load(data_file, cls=JSONDecoder)
                        # if "api_used" in jsonData:
                        #         self._api_used = jsonData["api_used"]
                        _LOGGER.debug(f"SOLCAST - load_saved_data file exists.. file type is {type(jsonData)}")
                        if jsonData.get("version", 1) == _JSON_VERSION:
                            loadedData = True
                            self._data = jsonData
                            
                            #any site changes that need to be removed
                            for s in jsonData['siteinfo']:
                                if not any(d.get('resource_id', '') == s for d in self._sites):
                                    _LOGGER.info(f"Solcast rooftop resource id {s} no longer part of your system.. removing saved data from cached file")
                                    del jsonData['siteinfo'][s]
                    #create an up to date forecast and make sure the TZ fits just in case its changed                
                    await self.buildforcastdata()
                                    
                if not loadedData:
                    #no file to load
                    _LOGGER.debug(f"SOLCAST - load_saved_data there is no existing file with saved data to load")
                    #could be a brand new install of the integation so this is poll once now automatically
                    await self.http_data()
            else:
                _LOGGER.debug(f"SOLCAST - load_saved_data site count is zero! ")
        except json.decoder.JSONDecodeError:
            _LOGGER.error("SOLCAST - load_saved_data error: The cached data is corrupt")
        except Exception as e:
            _LOGGER.error("SOLCAST - load_saved_data error: %s", traceback.format_exc())

    async def force_api_poll(self, *args):
        _LOGGER.debug(f"SOLCAST - force_api_poll called.")
        await self.http_data()

    async def delete_solcast_file(self, *args):
        _LOGGER.debug(f"SOLCAST - service event to delete old solcast.json file")
        try:
            if file_exists(self._filename):
                os.remove(self._filename)
                await self.sites_data()
                await self.load_saved_data()
        except Exception:
            _LOGGER.error(f"SOLCAST - service event to delete old solcast.json file failed")
            
    async def get_forecast_list(self, *args):
        _LOGGER.debug(f"SOLCAST - service event to get forecasts list")
        try:
            #return json.dumps(self._dataenergy, indent = 4) 
            return self._dataforecasts
        except Exception:
            _LOGGER.error(f"SOLCAST - service event to get list of forecasts failed")

    def get_api_used_count(self):
        """Return API polling count for this UTC 24hr period"""
        try:
            # if self._apiallusedup:
            #     return "Exceeded API Allowance"
            return self._api_used
        except Exception:
            return None
        
    def get_api_limit(self):
        """Return API polling count for this UTC 24hr period"""
        try:
            # if self._apiallusedup:
            #     return "Exceeded API Allowance"
            return self._api_limit
        except Exception:
            return None

    def get_last_updated_datetime(self) -> dt:
        """Return date time with the data was last updated"""
        try:
            return dt.fromisoformat(self._data["last_updated"])
        except Exception:
            _LOGGER.debug(f"SOLCAST - get_last_update_datetime try failed so returning year 2000")
            return None # dt.now(timezone.utc).replace(year=2000,month=1,day=1).isoformat()

    # async def reset_api_counter(self):
    #     try:
    #         _LOGGER.debug(f"SOLCAST - API counter reset to zero in reset_api_counter code")
    #         _LOGGER.debug(f"SOLCAST - UTC midnight is when the counter resets to 0")
    #         self._apiallusedup = False
    #         self._api_used = 0

    #         self._data['api_used'] = self._api_used

    #         with open(self._filename, 'w') as f:
    #             json.dump(self._data, f, ensure_ascii=False, cls=DateTimeEncoder)

    #     except Exception as e:
    #         _LOGGER.error("SOLCAST - reset_api_counter error: %s", traceback.format_exc())

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
            da = dt.now(self._tz).replace(second=0, microsecond=0)
            h = da.hour
            da = da.date()
            g = [d for d in self._tzdataconverted if d['period_start'].date() == da]
            tot = 0
            for p in g:
                if p["period_start"].hour >= h:
                    tot += p["pv_estimate"]
            
            return round(tot,2)
        except Exception:
            return 0
        
    def get_forecast_future_day(self, futureday = 1) -> dict[str, Any]:
        """Return Solcast Forecasts data for tomorrow"""
        try:
            da = dt.now(self._tz).replace(second=0, microsecond=0).date() + timedelta(days=futureday)
            h = [d for d in self._detailedForecasts if d['period_start'].date() == da]
            return {"detailedForecast":         h,
                    "dayname":da.strftime("%A")}
        except Exception:
            return {}

    def get_forecast_this_hour(self) -> int:
        try:
            da = dt.now(self._tz).replace(second=0, microsecond=0)
            g = [d for d in self._tzdataconverted if d['period_start'].day == da.day and d['period_start'].hour == da.hour]   
            return int(g[0]['pv_estimate'] * 1000)
        except Exception:
            return 0

    def get_forecast_next_hour(self) -> int:
        try:
            da = dt.now(self._tz).replace(second=0, microsecond=0) + timedelta(hours=1)
            #g = [d for d in self._tzdataconverted if d['period_start'] == da]   
            g = [d for d in self._tzdataconverted if d['period_start'].day == da.day and d['period_start'].hour == da.hour]  
            return int(g[0]['pv_estimate'] * 1000)
        except Exception:
            return 0

    def get_total_kwh_forecast_today(self) -> float:
        """Return total kwh total for rooftop site today"""
        try:
            da = dt.now(self._tz).replace(second=0, microsecond=0).date()
            g = [d for d in self._tzdataconverted if d['period_start'].date() == da]
            return round(sum(z['pv_estimate'] for z in g if z),2)
        except Exception:
            return 0

    def get_peak_w_day(self, dayincrement) -> int:
        """Return hour of max kw for rooftop site N days ahead"""
        try:
            da = dt.now(self._tz).date() + timedelta(days=dayincrement)
            g = tuple(
                d
                for d in self._dataforecasts
                if d["period_start"].astimezone(self._tz).date() == da
            )
            m = max(z["pv_estimate"] for z in g)
            return int(m * 1000)
        except Exception:
            return None

    def get_peak_w_time_day(self, dayincrement) -> dt:
        """Return hour of max kw for rooftop site N days ahead"""
        try:
            da = dt.now(self._tz).date() + timedelta(days=dayincrement)
            g = tuple(
                d
                for d in self._dataforecasts
                if d["period_start"].astimezone(self._tz).date() == da
            )
            return max((z for z in g), key=lambda x: x["pv_estimate"])["period_start"]
        except Exception:
            return None
        
    def get_total_kwh_forecast_furture_for_day(self, dayincrement = 1) -> float:
        """Return total kwh total for rooftop site tomorrow"""
        try:
            da = dt.now(self._tz).replace(second=0, microsecond=0).date() + timedelta(days=dayincrement)
            g = [d for d in self._tzdataconverted if d['period_start'].date() == da]
            return round(sum(z['pv_estimate'] for z in g if z),2)
        except Exception:
            return 0

    def get_energy_data(self) -> dict[str, Any]:
        try:
            return self._dataenergy
        except Exception as e:
            _LOGGER.error(f"SOLCAST - get_energy_data: {e}")
            return None

    async def buildforcastdata(self):
        """build the data needed and convert where needed"""
        try:
            today = dt.now(self._tz).date()
            yesterday = dt.now(self._tz).date() + timedelta(days=-1)
            lastday = dt.now(self._tz).date() + timedelta(days=7)
            self._tzdataconverted = []
            self._detailedForecasts = []
            
            _forecasts = []
        
            for s in self._data['siteinfo']:
                tally = 0
                for x in self._data['siteinfo'][s]['forecasts']:
                    #loop each rooftop site and its forecasts
                    z = parse_datetime(x['period_end']) - timedelta(minutes=30)
                    zz = parse_datetime(x['period_end']).astimezone(self._tz) - timedelta(minutes=30)
                    
                    if zz.date() < lastday and zz.date() > yesterday:
                        if zz.date() == today:
                            tally += round(x["pv_estimate"]*0.5, 4)
                            
                        itm = next((item for item in _forecasts if item["period_start"] == z), None)
                        if itm:
                            itm["pv_estimate"] = round(itm["pv_estimate"] + x["pv_estimate"]*0.5, 4)
                            itm["pv_estimate10"] = round(itm["pv_estimate10"] + x["pv_estimate10"]*0.5, 4)
                            itm["pv_estimate90"] = round(itm["pv_estimate90"] + x["pv_estimate90"]*0.5, 4)
                        else:    
                            _forecasts.append({"period_start": z,"pv_estimate": x["pv_estimate"]*0.5,
                                                                "pv_estimate10": x["pv_estimate10"]*0.5,
                                                                "pv_estimate90": x["pv_estimate90"]*0.5})
                    # else:
                    #     _LOGGER.error(f"deleting item {x}")
                    #     self._data['siteinfo'][s]['forecasts'].remove(x)
                    
                        
                self._data['siteinfo'][s]['tally'] = round(tally, 2)
                        
            _forecasts = sorted(_forecasts, key=itemgetter("period_start"))     
            
            self._dataforecasts = _forecasts 
                    
            for x in _forecasts:
                zz = x['period_start'].astimezone(self._tz).replace(minute=0)
                itm = next((item for item in self._tzdataconverted if item["period_start"] == zz), None)
                if itm:
                    itm["pv_estimate"] = round(itm["pv_estimate"] + x["pv_estimate"], 4)
                    itm["pv_estimate10"] = round(itm["pv_estimate10"] + x["pv_estimate10"], 4)
                    itm["pv_estimate90"] = round(itm["pv_estimate90"] + x["pv_estimate90"], 4)
                else:    
                    self._tzdataconverted.append({"period_start": zz,"pv_estimate": x["pv_estimate"],
                                                        "pv_estimate10": x["pv_estimate10"],
                                                        "pv_estimate90": x["pv_estimate90"]})
                
            for x in _forecasts:
                #zz = x['period_start'].astimezone(self._tz).replace(minute=0)
                zz = x['period_start'].astimezone(self._tz)
                itm = next((item for item in self._detailedForecasts if item["period_start"] == zz), None)
                if itm:
                    itm["pv_estimate"] = round(itm["pv_estimate"] + x["pv_estimate"], 4)
                    itm["pv_estimate10"] = round(itm["pv_estimate10"] + x["pv_estimate10"], 4)
                    itm["pv_estimate90"] = round(itm["pv_estimate90"] + x["pv_estimate90"], 4)
                else:    
                    self._detailedForecasts.append({"period_start": zz,"pv_estimate": x["pv_estimate"],
                                                        "pv_estimate10": x["pv_estimate10"],
                                                        "pv_estimate90": x["pv_estimate90"]})
                

            self._dataenergy = {"wh_hours": self.makeenergydict()}
            
            with open(self._filename, 'w') as f:
                    json.dump(self._data, f, ensure_ascii=False, cls=DateTimeEncoder)
                
        except Exception as e:
            _LOGGER.error("SOLCAST - http_data error: %s", traceback.format_exc())
        
    
    async def http_data(self):
        """Request data via the Solcast API."""
        
        try:
            
            today = dt.now(self._tz).date()
            yesterday = dt.now(self._tz).date() + timedelta(days=-1)
            lastday = dt.now(self._tz).date() + timedelta(days=7)
  

            _s = {}

            _LOGGER.debug(f"SOLCAST - Polling Solcast API")

            for site in self._sites:
                _LOGGER.debug(f"SOLCAST - API polling for rooftop {site['resource_id']}")
                # _LOGGER.debug(f" getting site: {site['resource_id']}")
                #_data = []

                af = await self.fetch_data("forecasts", 168, site=site['resource_id'], apikey=site['apikey'])
                
                if not type(af) is dict:
                    _LOGGER.warning("SOLCAST - Data returned by Solcast API is not the correct format")
                    return
                if not "forecasts" in af:
                    _LOGGER.warning("SOLCAST - Data returned by Solcast API is not the correct format")
                    return

                
                _forecasts = [] 
                try:
                    _forecasts = self._data['siteinfo'][site['resource_id']]['forecasts']
                except:
                    pass
            
                for x in af["forecasts"]:
                    #loop each rooftop site and its forecasts
                    
                    itm = next((item for item in _forecasts if item["period_end"] == x['period_end']), None)
                    if itm:
                        itm["pv_estimate"] = round(x["pv_estimate"], 4)
                        itm["pv_estimate10"] = round(x["pv_estimate10"], 4)
                        itm["pv_estimate90"] = round(x["pv_estimate90"], 4)
                    else:    
                        # _LOGGER.debug("adding itm")
                        _forecasts.append({"period_end": x['period_end'],"pv_estimate": round(x["pv_estimate"], 4),
                                                                "pv_estimate10": round(x["pv_estimate10"], 4),
                                                                "pv_estimate90": round(x["pv_estimate90"], 4)})
                
                #this deletes data that is too old or not needed yet    
                for x in _forecasts:
                    zz = parse_datetime(x['period_end']).astimezone(self._tz) - timedelta(minutes=30)
                    if not (zz.date() < lastday and zz.date() > yesterday):
                        # _LOGGER.info("removing other x")
                        _forecasts.remove(x)
                
           
                _forecasts = sorted(_forecasts, key=itemgetter("period_end"))
                
                self._data['siteinfo'].update({site['resource_id']:{'forecasts': copy.deepcopy(_forecasts)}})


            self._data["last_updated"] = dt.now(timezone.utc).replace(second=0 ,microsecond=0).isoformat()
            #self._data['api_used'] = self._api_used
            await self.sites_usage()
            self._data['version'] = _JSON_VERSION

            await self.buildforcastdata()


        except Exception as e:
            _LOGGER.error("SOLCAST - http_data error: %s", traceback.format_exc())

    async def fetch_data(self, path= "error", hours=168, site="", apikey="") -> dict[str, Any]:
        """fetch data via the Solcast API."""
        
        try:
            params = {"format": "json", "api_key": apikey, "hours": hours}
            url=f"{self.options.host}/rooftop_sites/{site}/{path}"
            _LOGGER.debug(f"SOLCAST - fetch_data code url - {url}")

            async with async_timeout.timeout(60):
                apiCacheFileName = "forecasts_" + site + ".json"
                if self.apiCacheEnabled and file_exists(apiCacheFileName):
                    _LOGGER.debug(f"SOLCAST - Getting cached testing data for site {site}")
                    status = 404
                    with open(apiCacheFileName) as f:
                        resp_json = json.load(f)
                        status = 200
                        _LOGGER.debug(f"SOLCAST - Got cached file data for site {site}")
                else:
                    _LOGGER.debug(f"SOLCAST - OK REAL API CALL HAPPENING RIGHT NOW")
                    resp: ClientResponse = await self.aiohttp_session.get(
                        url=url, params=params, ssl=False
                    )
                    status = resp.status

                    if status == 200:
                        _LOGGER.debug(f"SOLCAST - API returned data. API Counter incremented from {self._api_used} to {self._api_used + 1}")
                        # self._api_used = self._api_used + 1
    
                    resp_json = await resp.json(content_type=None)

                    if self.apiCacheEnabled:
                        with open(apiCacheFileName, 'w') as f:
                            json.dump(resp_json, f, ensure_ascii=False)
                        
                _LOGGER.debug(f"SOLCAST - fetch_data code http_session returned data type is {type(resp_json)}")
                _LOGGER.debug(f"SOLCAST - fetch_data code http_session status is {status}")

            if status == 429:
                _LOGGER.warning("SOLCAST - Exceeded Solcast API allowed polling limit")
                #self._apiallusedup = True
                # self._api_used = 50
                #raise Exception(f"HTTP error: Exceeded Solcast API allowed polling limit")
            elif status == 400:
                _LOGGER.warning(
                    "SOLCAST - The rooftop site missing capacity, please specify capacity or provide historic data for tuning."
                )
                #raise Exception(f"HTTP error: The rooftop site missing capacity, please specify capacity or provide historic data for tuning.")
            elif status == 404:
                _LOGGER.warning("SOLCAST - Error 404. The rooftop site cannot be found or is not accessible.")
                #raise Exception(f"HTTP error: The rooftop site cannot be found or is not accessible.")
            elif status == 200:
                d = cast(dict, resp_json)
                _LOGGER.debug(f"SOLCAST - fetch_data Returned: {d}")
                return d
                #await self.format_json_data(d)
        except ConnectionRefusedError as err:
            _LOGGER.error("SOLCAST - Error. Connection Refused. %s",err)
        except ClientConnectionError as e:
            _LOGGER.error('SOLCAST - Connection Error', str(e))
        except asyncio.TimeoutError:
            _LOGGER.error("SOLCAST - Connection Timeout Error - Timed out connectng to Solcast API server")
        except Exception as e:
            _LOGGER.error("SOLCAST - fetch_data error: %s", traceback.format_exc())

        return None
    

    def makeenergydict(self) -> dict:
        wh_hours = {}
    
        try:
            lastv = -1
            lastk = -1
            for v in self._dataforecasts:
                d = v['period_start'].isoformat() #.isoformat()
                if v['pv_estimate'] == 0.0:
                    if lastv > 0.0:
                        wh_hours[d] = round(v['pv_estimate'] * 1000,0)
                    lastk = d
                    lastv = v['pv_estimate']
                else:
                    if lastv == 0.0:
                        #add the last one
                        wh_hours[lastk] = round(lastv * 1000,0)

                    wh_hours[d] = round(v['pv_estimate'] * 1000,0)
                    
                    lastk = d
                    lastv = v['pv_estimate']
        except Exception as e:
            _LOGGER.error("SOLCAST - makeenergydict: %s", traceback.format_exc())

        return wh_hours