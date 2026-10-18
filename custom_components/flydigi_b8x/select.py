"""Confirmed automatic/manual mode selection."""
from homeassistant.components.select import SelectEntity
from .entity import B8XEntity

MODES = {'自动调节': 0, '手动固定': 1}


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([B8XMode(entry.runtime_data)])


class B8XMode(B8XEntity, SelectEntity):
    _attr_options = list(MODES)
    _attr_icon = 'mdi:tune'

    def __init__(self, coordinator):
        super().__init__(coordinator, 'mode', '运行模式')

    @property
    def current_option(self):
        if not self.coordinator.data:
            return None
        return next((name for name, value in MODES.items()
                     if value == self.coordinator.data.mode_raw), None)

    async def async_select_option(self, option):
        await self.coordinator.async_control('mode', MODES[option])
