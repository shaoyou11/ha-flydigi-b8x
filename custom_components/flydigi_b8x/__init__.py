"""Local, bounded BLE access for Flydigi B8X."""
from homeassistant.const import Platform

from .coordinator import B8XCoordinator

DOMAIN = 'flydigi_b8x'
PLATFORMS = [Platform.SENSOR, Platform.LIGHT, Platform.NUMBER, Platform.SWITCH, Platform.SELECT]


async def async_setup_entry(hass, entry):
    coordinator = B8XCoordinator(hass, entry)
    entry.runtime_data = coordinator
    if coordinator.enabled:
        await coordinator.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass, entry):
    await entry.runtime_data.async_pause()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
