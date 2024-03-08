"""Constants for the Solcast Solar integration."""

from __future__ import annotations

from typing import Final

from homeassistant.helpers import selector

DOMAIN = "solcast_solar"
SOLCAST_URL = "https://api.solcast.com.au"


ATTR_ENTRY_TYPE: Final = "entry_type"
ENTRY_TYPE_SERVICE: Final = "service"

ATTRIBUTION: Final = "Data retrieved from Solcast"

CUSTOM_HOUR_SENSOR = "customhoursensor"

SERVICE_UPDATE = "update_forecasts"
SERVICE_CLEAR_DATA = "clear_all_solcast_data"
SERVICE_QUERY_FORECAST_DATA = "query_forecast_data"
SERVICE_SET_DAMPENING = "set_dampening"

# new 4.0.8 - integration config options menu
# new 4.0.15 - integration config options for custom hour (option 3)
CONFIG_OPTIONS = [
    selector.SelectOptionDict(value="configure_api", label="option1"),
    selector.SelectOptionDict(value="configure_dampening", label="option2"),
    selector.SelectOptionDict(value="configure_customsensor", label="option3"),
]
