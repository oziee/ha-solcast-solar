"""Support for Solcast PV forecast."""

import logging
import traceback

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.device_registry import async_get as device_registry

from .const import DOMAIN, SOLCAST_URL 
from .coordinator import SolcastUpdateCoordinator
from .solcastapi import ConnectionOptions, SolcastApi

PLATFORMS = ["sensor"]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up solcast parameters."""

    try:

        options = ConnectionOptions(
            entry.options[CONF_API_KEY],
            SOLCAST_URL
        )

        solcast = SolcastApi(hass, aiohttp_client.async_get_clientsession(hass), options)
        await solcast.sites_data()
        await solcast.load_saved_data()
        
        coordinator = SolcastUpdateCoordinator(hass, solcast)
        await coordinator.setup()

        await coordinator.async_config_entry_first_refresh()
        #await _async_migrate_unique_ids(hass, entry, coordinator)

        entry.async_on_unload(entry.add_update_listener(update_listener))

        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
        

        hass.config_entries.async_setup_platforms(entry, PLATFORMS)

        hass.bus.async_listen("solcast_update_all_forecasts", coordinator.service_event_update)

        return True

    except Exception as err:
        _LOGGER.error("async_setup_entry: %s",traceback.format_exc())
        return False

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

async def async_remove_config_entry_device(hass: HomeAssistant, entry: ConfigEntry, device) -> bool:
    device_registry(hass).async_remove_device(device.id)
    return True

async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener."""
    await hass.config_entries.async_reload(entry.entry_id)
