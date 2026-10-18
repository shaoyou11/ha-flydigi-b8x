"""Normal-mode settings only; protection and overclock controls excluded."""
from homeassistant.components.number import NumberEntity, NumberMode
from .entity import B8XEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([B8XNumber(entry.runtime_data, *spec) for spec in (
        ('wind', '风速设定', 4000, 4500, 100),
        ('cold', '制冷设定（原始值）', 92, 175, 1))])


class B8XNumber(B8XEntity, NumberEntity):
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator, kind, name, minimum, maximum, step):
        super().__init__(coordinator, kind, name)
        self.kind = kind
        self._attr_native_min_value = minimum
        self._attr_native_max_value = maximum
        self._attr_native_step = step
        self._attr_icon = 'mdi:fan' if kind == 'wind' else 'mdi:snowflake'
        if kind == 'wind':
            self._attr_native_unit_of_measurement = 'rpm'

    @property
    def available(self):
        return super().available and self.coordinator.data.mode_raw in (0, 1)

    @property
    def extra_state_attributes(self):
        if not self.coordinator.data:
            return None
        return {'control_type': '自动上限' if self.coordinator.data.mode_raw == 0 else '手动档位'}

    @property
    def native_value(self):
        return getattr(self.coordinator.data, self.kind + '_level', None)

    async def async_set_native_value(self, value):
        if value != int(value):
            raise ValueError('B8X level must be an integer')
        await self.coordinator.async_control(self.kind, int(value))
