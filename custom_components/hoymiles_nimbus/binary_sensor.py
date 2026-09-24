# custom_components/hoymiles_nimbus/binary_sensor.py

import logging
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass

from .hoymiles_client import HoymilesClient
from .device_registry import create_station_device_info

DOMAIN = "hoymiles_nimbus"

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Hoymiles binary sensors."""
    client = hass.data[DOMAIN][config_entry.entry_id]["client"]

    # Ensure the client is authenticated
    await hass.async_add_executor_job(client.login)

    _LOGGER.debug("Fetching station data for binary sensors...")
    stations = await hass.async_add_executor_job(client.select_by_page, "station")

    entities = []
    
    for station in stations:
        station_name = station.get('name', 'Unknown')
        sid = station.get("id")
        device_info = create_station_device_info(sid, station_name)

        entities.append(HoymilesStationOnlineSensor(client, station_name, sid, device_info))

    _LOGGER.debug(f"Created {len(entities)} binary sensor(s) for Hoymiles stations")
    async_add_entities(entities)


class HoymilesStationOnlineSensor(BinarySensorEntity):
    """Binary sensor to show if all DTUs in a station are online."""
    
    def __init__(self, client, station_name, sid, device_info):
        self._client = client
        self._sid = sid
        self._attr_name = f"{station_name} Fully Online"
        self._attr_unique_id = f"hoymiles_nimbus_{sid}_fully_online"
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
        self._attr_device_info = device_info
        self._attr_icon = "mdi:lan-connect"
        self._state = None
        self._dtu_count = 0

    @property
    def is_on(self):
        """Return true if all DTUs are online."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return additional state attributes."""
        return {
            "dtu_count": self._dtu_count,
        }

    async def async_update(self):
        """Fetch DTU connection status."""
        try:
            # Fetch device tree to check DTU status
            tree_data = await self.hass.async_add_executor_job(
                self._client.select_device_of_tree, self._sid
            )
            dtus = self._client.parse_dtu_info(tree_data)
            
            self._dtu_count = len(dtus)
            
            # Check if all DTUs are connected
            if not dtus:
                self._state = False
                _LOGGER.debug(f"Station {self._sid}: No DTUs found")
            else:
                self._state = all(dtu.get('connect', False) for dtu in dtus)
                online_count = sum(1 for dtu in dtus if dtu.get('connect', False))
                _LOGGER.debug(
                    f"Station {self._sid}: {online_count}/{len(dtus)} DTUs online. "
                    f"Fully online: {self._state}"
                )
                
        except Exception as e:
            _LOGGER.warning(f"Failed to update DTU status for station {self._sid}: {e}")
            self._state = None
