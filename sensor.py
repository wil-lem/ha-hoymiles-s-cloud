# custom_components/hoymiles_cloud/sensor.py

import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfPower, UnitOfEnergy  # Updated imports for units

from .hoymiles_client import HoymilesClient

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    client = hass.data["hoymiles_cloud"][config_entry.entry_id]

    # Ensure the client is authenticated
    # _LOGGER.debug("Logging into Hoymiles S-Cloud...")
    _LOGGER.warning("Does this show up?")
    await hass.async_add_executor_job(client.login)

    # _LOGGER.debug("Fetching stations from Hoymiles S-Cloud...")
    stations = await hass.async_add_executor_job(client.select_by_page, "station")

    # _LOGGER.debug(f"Found {len(stations)} stations")

    entities = []
    for station in stations:
        name = f"Hoymiles S-Cloud Station {station.get('name', 'Unknown')}"
        sid = station.get("id")
        station_id_str = f"hoymiles_station_{sid}"

        device_info = {
            "identifiers": {(station_id_str,)},
            "name": name,
            "manufacturer": "Hoymiles",
            "model": "X-Series",
        }

        entities.append(HoymilesStationPowerSensor(client, name, sid, device_info))
        entities.append(HoymilesStationEnergySensor(client, name, sid, device_info))

    async_add_entities(entities)

class HoymilesStationPowerSensor(SensorEntity):
    def __init__(self, client, name, sid, device_info):
        self._client = client
        self._sid = sid
        self._attr_name = f"{name} Current Power"
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_unique_id = f"hoymiles_scloud_{sid}_power"
        self._attr_device_class = "power"
        self._attr_device_info = device_info
        self._state = None

    @property
    def native_value(self):
        return self._state

    async def async_update(self):
        # _LOGGER.debug(f"Fetching current power for station {self._sid}")
        
        # Fetch the current power data from the Hoymiles S-Cloud
        data = await self.hass.async_add_executor_job(self._client.count_station_real_data, self._sid)
        # _LOGGER.debug(f"Received power data for station {self._sid}: {data}")
        val = data.get("data", {}).get("real_power", 0)
        if val is None:
            _LOGGER.warning(f"Received None value for power data for station {self._sid}")
            self._state = 0
        else:
            # _LOGGER.debug(f" Current power for station {self._sid}: {val}")
            self._state = float(val)
        
class HoymilesStationEnergySensor(SensorEntity):
    def __init__(self, client, name, sid, device_info):
        self._client = client
        self._sid = sid
        self._attr_name = f"{name} Daily Energy"
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_unique_id = f"hoymiles_scloud_{sid}_energy"
        self._attr_device_class = "energy"
        self._attr_state_class = "total_increasing"
        self._attr_icon = "mdi:solar-power"
        self._attr_device_info = device_info
        self._state = None

    @property
    def native_value(self):
        return self._state

    async def async_update(self):
        data = await self.hass.async_add_executor_job(self._client.count_station_real_data, self._sid)
        # _LOGGER.debug(f"Received energy data for station {self._sid}: {data}")
        val = data.get("data", {}).get("today_eq", 0)
        if val is None:
            _LOGGER.warning(f"Received None value for energy data for station {self._sid}")
            self._state = 0
        else:
            # _LOGGER.debug(f" Daily energy for station {self._sid}: {val}")
            # Convert to kWh
            # Assuming the value is in Wh, convert to kWh
            self._state = float(val) / 1000
