"""Persisted communication pause, independent of the cooler power state."""
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity import EntityCategory
from .entity import B8XEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([B8XConnection(entry.runtime_data)])


class B8XConnection(B8XEntity, SwitchEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = 'mdi:bluetooth-connect'

    def __init__(self, coordinator):
        super().__init__(coordinator, 'connection', '蓝牙连接')

    @property
    def available(self):
        return True

    @property
    def is_on(self):
        return self.coordinator.enabled

    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_set_enabled(True)

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_set_enabled(False)
