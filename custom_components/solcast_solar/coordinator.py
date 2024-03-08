"""The Solcast Solar integration."""

from __future__ import annotations

import logging
import traceback

from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_utc_time_change

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .solcastapi import SolcastApi

_LOGGER = logging.getLogger(__name__)


class SolcastUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from Solcast Solar API."""

    def __init__(self, hass: HomeAssistant, solcast: SolcastApi, version: str) -> None:
        """Initialize."""
        self.solcast = solcast
        self._hass = hass
        self._previousenergy = None
        self._version = version

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
        )

    async def _async_update_data(self):
        """Update data via library."""
        return self.solcast._data

    async def setup(self):
        d = {}
        self._previousenergy = d

        try:
            async_track_utc_time_change(
                self._hass, self.update_integration_listeners, second=0
            )
        except Exception:
            _LOGGER.error(
                "SOLCAST - Error coordinator setup: %s", traceback.format_exc()
            )

    async def update_integration_listeners(self, *args):
        try:
            self.async_update_listeners()
        except Exception:
            # _LOGGER.error("SOLCAST - update_integration_listeners: %s", traceback.format_exc())
            pass

    async def service_event_update(self, *args):
        await self.solcast.http_data(dopast=False)
        await self.update_integration_listeners()

    async def service_event_delete_old_solcast_json_file(self, *args):
        await self.solcast.delete_solcast_file()

    async def service_query_forecast_data(self, *args) -> tuple:
        return await self.solcast.get_forecast_list(*args)

    def get_energy_tab_data(self):
        return self.solcast.get_energy_data()

    def get_sensor_value(self, key=""):
        if key == "total_kwh_forecast_today":
            return self.solcast.get_total_kwh_forecast_day(0)
        elif key == "peak_w_today":
            return self.solcast.get_peak_w_day(0)
        elif key == "peak_w_time_today":
            return self.solcast.get_peak_w_time_day(0)
        elif key == "forecast_this_hour":
            return self.solcast.get_forecast_n_hour(0)
        elif key == "forecast_next_hour":
            return self.solcast.get_forecast_n_hour(1)
        elif key == "forecast_custom_hour":
            return self.solcast.get_forecast_custom_hour(self.solcast._customhoursensor)
        elif key == "forecast_next_12hour":
            return self.solcast.get_forecast_n_hour(12)
        elif key == "forecast_next_24hour":
            return self.solcast.get_forecast_n_hour(24)
        elif key == "total_kwh_forecast_tomorrow":
            return self.solcast.get_total_kwh_forecast_day(1)
        elif key == "total_kwh_forecast_d3":
            return self.solcast.get_total_kwh_forecast_day(2)
        elif key == "total_kwh_forecast_d4":
            return self.solcast.get_total_kwh_forecast_day(3)
        elif key == "total_kwh_forecast_d5":
            return self.solcast.get_total_kwh_forecast_day(4)
        elif key == "total_kwh_forecast_d6":
            return self.solcast.get_total_kwh_forecast_day(5)
        elif key == "total_kwh_forecast_d7":
            return self.solcast.get_total_kwh_forecast_day(6)
        elif key == "power_now":
            return self.solcast.get_power_production_n_mins(0)
        elif key == "power_now_30m":
            return self.solcast.get_power_production_n_mins(30)
        elif key == "power_now_1hr":
            return self.solcast.get_power_production_n_mins(60)
        elif key == "power_now_12hr":
            return self.solcast.get_power_production_n_mins(60 * 12)
        elif key == "power_now_24hr":
            return self.solcast.get_power_production_n_mins(60 * 24)
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

        # just in case
        return None

    def get_sensor_extra_attributes(self, key=""):
        if key == "total_kwh_forecast_today":
            return self.solcast.get_forecast_day(0)
        elif key == "total_kwh_forecast_tomorrow":
            return self.solcast.get_forecast_day(1)
        elif key == "total_kwh_forecast_d3":
            return self.solcast.get_forecast_day(2)
        elif key == "total_kwh_forecast_d4":
            return self.solcast.get_forecast_day(3)
        elif key == "total_kwh_forecast_d5":
            return self.solcast.get_forecast_day(4)
        elif key == "total_kwh_forecast_d6":
            return self.solcast.get_forecast_day(5)
        elif key == "total_kwh_forecast_d7":
            return self.solcast.get_forecast_day(6)

        # just in case
        return None

    def get_site_sensor_value(self, roof_id, key):
        match key:
            case "site_data":
                return self.solcast.get_rooftop_site_total_today(roof_id)
            case _:
                return None

    def get_site_sensor_extra_attributes(self, roof_id, key):
        match key:
            case "site_data":
                return self.solcast.get_rooftop_site_extra_data(roof_id)
            case _:
                return None
