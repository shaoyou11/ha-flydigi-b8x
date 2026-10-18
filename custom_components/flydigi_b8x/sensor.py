"""Measured temperatures and speed from B8X notifications."""
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfTemperature
from .entity import B8XEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([B8XSensor(entry.runtime_data, *spec) for spec in (
        ('cold_temperature', '冷面温度', UnitOfTemperature.CELSIUS),
        ('hot_temperature', '热面温度', UnitOfTemperature.CELSIUS),
        ('rpm', '风扇转速', 'rpm'))])


class B8XSensor(B8XEntity, SensorEntity):
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, key, name, unit):
        super().__init__(coordinator, key, name)
        self.key = key
        self._attr_native_unit_of_measurement = unit
        if key.endswith('temperature'):
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
        else:
            self._attr_icon = 'mdi:fan'

    @property
    def native_value(self):
        return getattr(self.coordinator.data, self.key, None)
