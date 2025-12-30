# custom_components/hoymiles_cloud/sensor.py

import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfPower, UnitOfEnergy, UnitOfElectricPotential, UnitOfElectricCurrent

from .hoymiles_client import HoymilesClient
from .device_registry import create_station_device_info, create_module_device_info

DOMAIN = "hoymiles_nimbus"

_LOGGER = logging.getLogger(__name__)


class HoymilesSystemCoordinator:
    """Coordinator to manage system data updates for all module sensors."""
    
    def __init__(self, hass, client, initial_system):
        self._hass = hass
        self._client = client
        self._system = initial_system
        self._last_update = None
        
    async def get_system(self):
        """Get the current system data, updating if needed."""
        import datetime
        now = datetime.datetime.now()
        
        # Update every 30 seconds to avoid too frequent API calls
        if (self._last_update is None or 
            (now - self._last_update).total_seconds() > 30):
            
            self._system = await self._hass.async_add_executor_job(self._client.map_system)
            await self._hass.async_add_executor_job(self._client.fill_system_data, self._system)
            self._last_update = now
            
        return self._system
    
    def find_module(self, station_id, module_id):
        """Find a specific module in the system."""
        for station in self._system:
            if station.station_id == station_id:
                for microinverter in station.microinverters:
                    for module in microinverter.modules:
                        if module.id == module_id:
                            return module
        return None


async def async_setup_entry(hass, config_entry, async_add_entities):
    client = hass.data[DOMAIN][config_entry.entry_id]

    # Ensure the client is authenticated
    await hass.async_add_executor_job(client.login)

    _LOGGER.warning("Fetching device data from Hoymiles S-Cloud...")
    stations = await hass.async_add_executor_job(client.select_by_page, "station")

    # Build system map with individual modules
    system = await hass.async_add_executor_job(client.map_system)
    await hass.async_add_executor_job(client.fill_system_data, system)

    _LOGGER.warning("Found %d station(s) in Hoymiles account", len(stations))

    entities = []
    
    # Create a shared system coordinator for all module sensors
    system_coordinator = HoymilesSystemCoordinator(hass, client, system)
    
    for station in stations:
        station_name = station.get('name', 'Unknown')
        sid = station.get("id")
        device_info = create_station_device_info(sid, station_name)
        name = device_info["name"]

        entities.append(HoymilesStationPowerSensor(client, name, sid, device_info))
        entities.append(HoymilesStationEnergySensor(client, name, sid, device_info))
        entities.append(HoymilesStationRatioSensor(client, name, sid, device_info))

    # Add individual solar module sensors
    for station in system:
        station_name = station.name
        sid = station.station_id
        station_identifier = f"hoymiles_station_{station.station_id}"

        for microinverter in station.microinverters:
            for module in microinverter.modules:
                module_name = f"{station_name} Panel {module.id}"
                
                # Create device info for the solar module
                module_device_info = create_module_device_info(module.id, station_identifier)
                
                # Add power, voltage, and current sensors for each module
                entities.append(HoymilesSolarModulePowerSensor(system_coordinator, module_name, station.station_id, module, module_device_info))
                entities.append(HoymilesSolarModuleVoltageSensor(system_coordinator, module_name, station.station_id, module, module_device_info))
                entities.append(HoymilesSolarModuleCurrentSensor(system_coordinator, module_name, station.station_id, module, module_device_info))

    _LOGGER.warning("Created %d sensors for Hoymiles devices", len(entities))
    async_add_entities(entities)

class HoymilesStationPowerSensor(SensorEntity):
    def __init__(self, client, name, sid, device_info):
        self._client = client
        self._sid = sid
        self._attr_name = f"{name} Current Power"
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_unique_id = f"hoymiles_nimbus_{sid}_power"
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
        self._attr_unique_id = f"hoymiles_nimbus_{sid}_energy"
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

class HoymilesStationRatioSensor(SensorEntity):
    def __init__(self, client, name, sid, device_info):
        self._client = client
        self._sid = sid
        self._attr_name = f"{name} Performance Ratio"
        self._attr_native_unit_of_measurement = "%"
        self._attr_unique_id = f"hoymiles_nimbus_{sid}_performance_ratio"
        self._attr_device_class = "performance_ratio"
        self._attr_state_class = "measurement"
        self._attr_icon = "mdi:percent"
        self._attr_device_info = device_info
        self._state = None

    @property
    def native_value(self):
        return self._state

    async def async_update(self):
        data = await self.hass.async_add_executor_job(self._client.count_station_real_data, self._sid)
        capacity = data.get("data", {}).get("capacitor", 0)
        current_power = data.get("data", {}).get("real_power", 0)

        if capacity is None:
            _LOGGER.warning(f"Received None value for capacity data for station {self._sid}")
            self._state = 0
            return
        if current_power is None:
            _LOGGER.warning(f"Received None value for current power data for station {self._sid}")
            self._state = 0
            return
        if capacity == 0:
            self._state = 0
        else:
            # Make sure we're dealing with floats
            capacity = float(capacity)
            current_power = float(current_power)
            capacity_kw = capacity * 1000  # Convert kW to W
            ratio = (current_power / capacity_kw) * 100
            self._state = round(ratio, 2)
        

class HoymilesSolarModulePowerSensor(SensorEntity):
    def __init__(self, coordinator, name, station_id, module, device_info):
        self._coordinator = coordinator
        self._station_id = station_id
        self._module_id = module.id
        self._attr_name = f"{name} Power"
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_unique_id = f"hoymiles_nimbus_module_{module.id}_power"
        self._attr_device_class = "power"
        self._attr_state_class = "measurement"
        self._attr_device_info = device_info
        self._attr_icon = "mdi:solar-panel"
        self._state = None

    @property
    def native_value(self):
        return self._state

    @property
    def extra_state_attributes(self):
        """Return additional state attributes."""
        module = self._coordinator.find_module(self._station_id, self._module_id)
        if module:
            attrs = {
                "module_id": module.id,
                "port": module.port,
                "position_x": module.x,
                "position_y": module.y,
            }
            if module.getLatestTime():
                attrs["last_updated"] = module.getLatestTime()
            return attrs
        return {}

    async def async_update(self):
        # Get updated system data through coordinator
        system = await self._coordinator.get_system()
        
        # Find our specific module in the updated system
        module = self._coordinator.find_module(self._station_id, self._module_id)
        if module:
            power = module.getCurrentPower()
            self._state = power if power is not None else 0
        else:
            # Module not found, set to 0
            self._state = 0


class HoymilesSolarModuleVoltageSensor(SensorEntity):
    def __init__(self, coordinator, name, station_id, module, device_info):
        self._coordinator = coordinator
        self._station_id = station_id
        self._module_id = module.id
        self._attr_name = f"{name} Voltage"
        self._attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
        self._attr_unique_id = f"hoymiles_nimbus_module_{module.id}_voltage"
        self._attr_device_class = "voltage"
        self._attr_state_class = "measurement"
        self._attr_device_info = device_info
        self._attr_icon = "mdi:flash"
        self._state = None

    @property
    def native_value(self):
        return self._state

    @property
    def extra_state_attributes(self):
        """Return additional state attributes."""
        module = self._coordinator.find_module(self._station_id, self._module_id)
        if module:
            attrs = {
                "module_id": module.id,
                "port": module.port,
                "position_x": module.x,
                "position_y": module.y,
            }
            if module.getLatestTime():
                attrs["last_updated"] = module.getLatestTime()
            return attrs
        return {}

    async def async_update(self):
        # Get updated system data through coordinator
        system = await self._coordinator.get_system()
        
        # Find our specific module in the updated system
        module = self._coordinator.find_module(self._station_id, self._module_id)
        if module:
            latest_data_point = module.getLatestDataPoint()
            if latest_data_point and latest_data_point.volt is not None:
                self._state = float(latest_data_point.volt)
            else:
                self._state = 0
        else:
            # Module not found, set to 0
            self._state = 0


class HoymilesSolarModuleCurrentSensor(SensorEntity):
    def __init__(self, coordinator, name, station_id, module, device_info):
        self._coordinator = coordinator
        self._station_id = station_id
        self._module_id = module.id
        self._attr_name = f"{name} Current"
        self._attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
        self._attr_unique_id = f"hoymiles_nimbus_module_{module.id}_current"
        self._attr_device_class = "current"
        self._attr_state_class = "measurement"
        self._attr_device_info = device_info
        self._attr_icon = "mdi:current-ac"
        self._state = None

    @property
    def native_value(self):
        return self._state

    @property
    def extra_state_attributes(self):
        """Return additional state attributes."""
        module = self._coordinator.find_module(self._station_id, self._module_id)
        if module:
            attrs = {
                "module_id": module.id,
                "port": module.port,
                "position_x": module.x,
                "position_y": module.y,
            }
            if module.getLatestTime():
                attrs["last_updated"] = module.getLatestTime()
            return attrs
        return {}

    async def async_update(self):
        # Get updated system data through coordinator
        system = await self._coordinator.get_system()
        
        # Find our specific module in the updated system
        module = self._coordinator.find_module(self._station_id, self._module_id)
        if module:
            latest_data_point = module.getLatestDataPoint()
            if latest_data_point and latest_data_point.ampere is not None:
                self._state = float(latest_data_point.ampere)
            else:
                self._state = 0
        else:
            # Module not found, set to 0
            self._state = 0
