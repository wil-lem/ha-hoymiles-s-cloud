import logging
from datetime import datetime, timedelta
from homeassistant.components.number import NumberEntity
from homeassistant.const import CONF_SCAN_INTERVAL
from .hoymiles_client import HoymilesClient
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Define the throttling interval (5 minutes)
UPDATE_INTERVAL = timedelta(seconds=30)

SCAN_INTERVAL = timedelta(seconds=30)

async def async_setup_entry(hass, config_entry, async_add_entities):
    client = hass.data[DOMAIN][config_entry.entry_id]

    _LOGGER.debug("[numbers] Logging into Hoymiles S-Cloud...")
    await hass.async_add_executor_job(client.login)

    _LOGGER.debug("[numbers] Fetching stations from Hoymiles S-Cloud...")
    stations = await hass.async_add_executor_job(client.select_by_page, "station")

    _LOGGER.debug(f"[numbers] Found {len(stations)} stations")

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

        entities.append(HoymilesMicroInverterLevel(client, name, sid, device_info))

    async_add_entities(entities)

class HoymilesMicroInverterLevel(NumberEntity):
    """Representation of a Hoymiles power level sensor."""
    def __init__(self, client, name, sid, device_info):
        _LOGGER.debug(f"[numbers] Creating HoymilesMicroInverterLevel entity for {name} with SID {sid}")
        self._client = client
        self._sid = sid
        self._attr_name = f"{name} Power Level (%)"
        self._attr_unique_id = f"hoymiles_{sid}_power_level"
        self._attr_min_value = 5
        self._attr_max_value = 100
        self._attr_step = 1
        self._attr_native_value = 100
        self._attr_device_info = device_info
        self._attr_icon = "mdi:power-socket-eu"

        self._attr_should_poll = True

        self._last_write = datetime.min
        self._write_interval = timedelta(seconds=30)
        self._pending_value = None

     

    async def async_set_native_value(self, value):
        """Set the power level of the inverter."""
        now = datetime.now()

        if now - self._last_write < self._write_interval:
            _LOGGER.info(f"[numbers] Throttling: storing {value}% to apply later")
            self._pending_value = value
            self._attr_native_value = value
            self.async_write_ha_state() 
            return
        await self._apply_power_limit(value)

        # If a pending value exists and is different, schedule it after delay
        if self._pending_value is not None and self._pending_value != value:
            delay = (self._last_write + self._write_interval - now).total_seconds()
            self.hass.loop.call_later(delay, self._schedule_pending_write)


    async def _apply_power_limit(self, value):
        _LOGGER.debug(f"[numbers] Applying power limit: {value}%")
        self._attr_native_value = value
        await self.hass.async_add_executor_job(self._client.set_power_limit, self._sid, value)
        self._last_write = datetime.now()
        self.async_write_ha_state()


    def _schedule_pending_write(self):
        if self._pending_value is not None:
            value = self._pending_value
            self._pending_value = None
            _LOGGER.info(f"[numbers] Executing delayed write of {value}%")
            self.hass.async_create_task(self._apply_power_limit(value))


    async def async_update(self):
        """Fetch the latest state of the inverter."""
        
        _LOGGER.debug(f"[numbers] Updating power level for SID {self._sid}")

        station = await self.hass.async_add_executor_job(self._client.findStation, self._sid)
        if not station:
            _LOGGER.warning(f"[numbers] Station with SID {self._sid} not found")
            return
        
        _LOGGER.debug(f"[numbers] Station data: {station}")
        config = station.get("config")
        if not config:
            _LOGGER.warning(f"[numbers] No configuration found for station with SID {self._sid}")
            return
        _LOGGER.debug(f"[numbers] Station configuration: {config}")
        power_level = config.get("power_limit")
        if power_level is None:
            _LOGGER.warning(f"[numbers] No power level found for station with SID {self._sid}")
            return
        _LOGGER.debug(f"[numbers] Power level for station with SID {self._sid}: {power_level}")
    
        self._attr_native_value = power_level
        