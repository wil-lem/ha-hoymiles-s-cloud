
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .hoymiles_client import HoymilesClient  # Import the client class


DOMAIN = "hoymiles_cloud"
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    client = HoymilesClient(
        username=entry.data["username"],
        password=entry.data["password"],
        base_url=entry.data.get("base_url", "https://neapi.hoymiles.com/"),
    )

    
    hass.data[DOMAIN][entry.entry_id] = client
    _LOGGER.debug("Hoymiles Cloud config entry setup complete: %s", entry.data)  
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "number"])

    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    await hass.config_entries.async_forward_entry_unload(entry, "number")
    # Clean up the client instance
    hass.data[DOMAIN].pop(entry.entry_id)
    return True

