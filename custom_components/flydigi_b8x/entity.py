"""Shared device identity and confirmed-state availability."""
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity


class B8XEntity(CoordinatorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, key, name):
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.address + '_' + key
        self._attr_name = name
        self._attr_device_info = DeviceInfo(
            identifiers={('flydigi_b8x', coordinator.address)},
            name='Flydigi B8X', manufacturer='Flydigi', model='B8X')

    @property
    def available(self):
        return self.coordinator.enabled and super().available and self.coordinator.data is not None
