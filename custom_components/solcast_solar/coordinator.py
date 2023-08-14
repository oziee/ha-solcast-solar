"""The Solcast Solar integration."""
from __future__ import annotations

import logging
import traceback
from contextlib import suppress
from datetime import timedelta

import async_timeout
import homeassistant.util.dt as dt_util
from homeassistant.components.recorder import get_instance, history
from homeassistant.const import MAJOR_VERSION, MINOR_VERSION
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.event import async_track_utc_time_change
from homeassistant.helpers.sun import (get_astral_location,
                                       get_location_astral_event_next)
from homeassistant.helpers.update_coordinator import (DataUpdateCoordinator,
                                                      UpdateFailed)

from .const import DOMAIN
from .solcastapi import SolcastApi

_LOGGER = logging.getLogger(__name__)

class SolcastUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from Solcast Solar API."""

    def __init__(self, hass: HomeAssistant, solcast: SolcastApi) -> None:
        """Initialize."""
        self.solcast = solcast
        self._hass = hass
        self._previousenergy = None
        self._version = ""

        self._v = f"{MAJOR_VERSION}.{MINOR_VERSION}"

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
        )


    async def _async_update_data(self):
        """Update data via library."""
        return self.solcast._data

    # async def reset_api_counter(self, *args):
    #     try:
    #         _LOGGER.debug("SOLCAST - resetting api counter")
    #         await self.solcast.reset_api_counter()
    #     except Exception as error:
    #         _LOGGER.error("SOLCAST - Error resetting API counter")
            
    async def reset_past_data(self, *args):
        try:
            _LOGGER.debug("SOLCAST - resetting past data")
            await get_instance(self._hass).async_add_executor_job(self.gethistory)
        except Exception as error:
            _LOGGER.error("SOLCAST - reset_past_data: Error resetting past data")

    async def setup(self):
        try:
            _LOGGER.debug("SOLCAST - setting up the coordinator")
            await get_instance(self._hass).async_add_executor_job(self.gethistory)
        except Exception:
            _LOGGER.error("SOLCAST - Error coordinator setup to get past history data")
            d={}
            self._previousenergy = d

        try:
            #async_track_utc_time_change(self._hass, self.reset_api_counter, hour=0, minute=0, second=0, local=False)
            async_track_utc_time_change(self._hass, self.reset_past_data, hour=0, minute=0, second=30, local=True)
            async_track_utc_time_change(self._hass, self.update_integration_listeners, minute=0, second=15, local=True)
        except Exception as error:
            _LOGGER.error("SOLCAST - Error coordinator setup: %s", traceback.format_exc())

    async def update_integration_listeners(self,*args):
        try:
            self.async_update_listeners()
        except Exception:
            _LOGGER.error("SOLCAST - update_integration_listeners: %s", traceback.format_exc())


    async def service_event_update(self, *args):
        _LOGGER.info("SOLCAST - Event called to force an update of data from Solcast API")
        await self.solcast.force_api_poll()
        await self.update_integration_listeners()

    async def service_event_delete_old_solcast_json_file(self, *args):
        _LOGGER.info("SOLCAST - Event called to delete the solcast.json file. The data will poll the Solcast API refresh")
        await self.solcast.delete_solcast_file()

    async def service_get_forecasts(self, *args) -> str:
        _LOGGER.info("SOLCAST - Event called to get list of forecasts")
        d = await self.solcast.get_forecast_list()
        return d
        
    def get_energy_tab_data(self):
        return self.solcast.get_energy_data()

    def get_sensor_value(self, key=""):
        if key == "total_kwh_forecast_today":
            return self.solcast.get_total_kwh_forecast_today()
        elif key == "peak_w_today":
            return self.solcast.get_peak_w_day(0)
        elif key == "peak_w_time_today":
            return self.solcast.get_peak_w_time_day(0)
        elif key == "forecast_this_hour":
            return self.solcast.get_forecast_this_hour()
        elif key == "forecast_next_hour":
            return self.solcast.get_forecast_next_hour()
        elif key == "total_kwh_forecast_tomorrow":
            return self.solcast.get_total_kwh_forecast_furture_for_day(1) 
        elif key == "total_kwh_forecast_d3":
            return self.solcast.get_total_kwh_forecast_furture_for_day(2)
        elif key == "total_kwh_forecast_d4":
            return self.solcast.get_total_kwh_forecast_furture_for_day(3)
        elif key == "total_kwh_forecast_d5":
            return self.solcast.get_total_kwh_forecast_furture_for_day(4)
        elif key == "total_kwh_forecast_d6":
            return self.solcast.get_total_kwh_forecast_furture_for_day(5)
        elif key == "total_kwh_forecast_d7":
            return self.solcast.get_total_kwh_forecast_furture_for_day(6)
        elif key == "peak_w_tomorrow":
            return self.solcast.get_peak_w_day(1)
        elif key == "peak_w_time_tomorrow":
            return self.solcast.get_peak_w_time_day(1)
        elif key == "get_remaining_today":
            return self.solcast.get_remaining_today()
        elif key == "api_counter":
            return self.solcast.get_api_used_count()
        elif key == "api_limit":
            return self.solcast.get_api_limit()
        elif key == "lastupdated":
            return self.solcast.get_last_updated_datetime()

        #just in case
        return None

    def get_sensor_extra_attributes(self, key=""):
        if key == "total_kwh_forecast_today":
            return self.solcast.get_forecast_future_day(0)
        elif key == "total_kwh_forecast_tomorrow":
            return self.solcast.get_forecast_future_day(1)
        elif key == "total_kwh_forecast_d3":
            return self.solcast.get_forecast_future_day(2)
        elif key == "total_kwh_forecast_d4":
            return self.solcast.get_forecast_future_day(3)
        elif key == "total_kwh_forecast_d5":
            return self.solcast.get_forecast_future_day(4)
        elif key == "total_kwh_forecast_d6":
            return self.solcast.get_forecast_future_day(5)
        elif key == "total_kwh_forecast_d7":
            return self.solcast.get_forecast_future_day(6)

        #just in case
        return None

    def get_site_value(self, key=""):
        return self.solcast.get_rooftop_site_total_today(key)

    def get_site_extra_attributes(self, key=""):
        return self.solcast.get_rooftop_site_extra_data(key)
        
    def gethistory(self):
        try:
            # start_date = dt_util.now().astimezone().replace(hour=0,minute=0,second=0,microsecond=0) - timedelta(days=7)
            # end_date = dt_util.now().astimezone().replace(hour=23,minute=59,second=59,microsecond=0) - timedelta(days=1)
            
            #start_date = dt_util.as_utc(dt_util.now().replace(hour=0,minute=0,second=0,microsecond=0)) - timedelta(days=7)
            start_date = dt_util.as_utc(dt_util.now().replace(hour=0,minute=0,second=0,microsecond=0)) - timedelta(days=1000)
            #end_date = dt_util.as_utc(dt_util.now().replace(hour=23,minute=59,second=59,microsecond=0)) - timedelta(days=1)
            
            #_LOGGER.debug(f"SOLCAST - gethistory: from UTC - {start_date} to - {end_date}")
            _LOGGER.debug(f"SOLCAST - gethistory")

            lower_entity_id = "sensor.forecast_this_hour"

            history_list = history.state_changes_during_period(
                self._hass,
                start_time=start_date,
                #end_time=end_date,
                entity_id=lower_entity_id,
                no_attributes=True,
                descending=True,
            )

            d={}
            for state in history_list.get(lower_entity_id, []):
                # filter out all None, NaN and "unknown" states
                # only keep real values
                with suppress(ValueError):
                    #d[state.last_updated.replace(minute=0,second=0,microsecond=0).astimezone().isoformat()] = float(state.state)
                    if float(state.state) > 0 :
                        d[state.last_updated.replace(minute=0,second=0,microsecond=0).isoformat()] = float(state.state)

            _LOGGER.debug(f"SOLCAST - gethistory got {len(d)} items")
            _LOGGER.debug(f"{d}")
                
            self._previousenergy = d
        except Exception:
            _LOGGER.error("SOLCAST - gethistory: %s", traceback.format_exc())