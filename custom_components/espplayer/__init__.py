"""
Support for Esp Media Player.

Developed by @dscao
"""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, CONF_SCAN_INTERVAL, CONF_NAME
from homeassistant.core import HomeAssistant
from .const import CONF_SENSORSTATE, CONF_ESPPLAY, CONF_ESPSTOP, CONF_ESPVOL, DOMAIN

import logging

PLATFORMS = ["media_player"]
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    config = entry.data
    name = config[CONF_NAME]
    sensorstate = config[CONF_SENSORSTATE]
    espplay = config[CONF_ESPPLAY]
    espstop = config[CONF_ESPSTOP]
    hass.data.setdefault(DOMAIN, {})
    
    hass.data[DOMAIN][entry.entry_id] = espplay

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS
    )
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        if len(hass.config_entries.async_entries(DOMAIN)) == 0:
            hass.data.pop(DOMAIN)
    
    return unload_ok

