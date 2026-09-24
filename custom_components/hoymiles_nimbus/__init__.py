
"""The Hoymiles S-Cloud integration."""
from __future__ import annotations

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from .hoymiles_client import HoymilesClient
from homeassistant.helpers import device_registry as dr
from homeassistant.core import callback

DOMAIN = "hoymiles_nimbus"
PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.NUMBER, Platform.BINARY_SENSOR]

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Hoymiles S-Cloud from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    client = HoymilesClient(
        username=entry.data["username"],
        password=entry.data["password"],
        base_url=entry.data.get("base_url", "https://neapi.hoymiles.com/"),
    )

    hass.data[DOMAIN].setdefault(entry.entry_id, {})
    hass.data[DOMAIN][entry.entry_id]["client"] = client
    hass.data[DOMAIN][entry.entry_id].setdefault("device_map", {})

    dev_reg = dr.async_get(hass)

    # Fetch stations and register parent devices ahead of platform entity setup.
    # Note: 'via_device' is deprecated in HA 2026.8+ and removed in 2027.8;
    # parent device entry IDs are registered here and mapped for 'via_device_id'.
    try:
        await hass.async_add_executor_job(client.login)
        stations = await hass.async_add_executor_job(client.select_by_page, "station")
    except Exception as err:
        _LOGGER.warning("Could not pre-fetch stations for device registry: %s", err)
        stations = []

    for station in stations:
        sid = station.get("id")
        station_name = station.get("name", "Unknown")
        identifier = (f"hoymiles_station_{sid}",)

        # Create or get the device in the registry using plain fields (no deprecated created_at/modified_at/default_*).
        device_entry = dev_reg.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={identifier},
            name=f"Hoymiles Station {station_name}",
            manufacturer="Hoymiles",
            model="X-Series",
        )

        hass.data[DOMAIN][entry.entry_id]["device_map"][f"hoymiles_station_{sid}"] = device_entry.id

    # Store the client top-level for backward compatibility
    hass.data[DOMAIN][entry.entry_id]["client"] = client
    _LOGGER.debug("Hoymiles Cloud config entry setup complete: %s", entry.data)
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok

