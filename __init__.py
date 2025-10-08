
"""The Hoymiles S-Cloud integration."""
from __future__ import annotations

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from .hoymiles_client import HoymilesClient

DOMAIN = "hoymiles_nimbus"
PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.NUMBER]

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Hoymiles S-Cloud from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    client = HoymilesClient(
        username=entry.data["username"],
        password=entry.data["password"],
        base_url=entry.data.get("base_url", "https://neapi.hoymiles.com/"),
    )

    hass.data[DOMAIN][entry.entry_id] = client
    _LOGGER.debug("Hoymiles Cloud config entry setup complete: %s", entry.data)
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok

