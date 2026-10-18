"""B8X light with confirmed on/off state, no guessed RGB frames."""
from homeassistant.components.light import LightEntity, ColorMode
from .entity import B8XEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([B8XLight(entry.runtime_data)])


class B8XLight(B8XEntity, LightEntity):
    _attr_color_mode = ColorMode.ONOFF
    _attr_supported_color_modes = {ColorMode.ONOFF}

    def __init__(self, coordinator):
        super().__init__(coordinator, 'light', '灯光')

    @property
    def is_on(self):
        return self.coordinator.data.light if self.coordinator.data else None

    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_control('light', True)

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_control('light', False)
