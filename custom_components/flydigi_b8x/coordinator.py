"""Never retain a BLE connection between transactions."""
import asyncio
import contextlib
import logging
from datetime import timedelta

from bleak_retry_connector import BleakClientWithServiceCache, establish_connection
from homeassistant.components import bluetooth
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .session import exchange

_LOGGER = logging.getLogger(__name__)


class B8XCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        super().__init__(hass, _LOGGER, name='Flydigi B8X', config_entry=entry,
                         update_interval=timedelta(seconds=120))
        self.entry = entry
        self.address = entry.data['address']
        self.enabled = entry.data.get('connection_enabled', True)
        self._lock = asyncio.Lock()
        self._active = None

    async def _transaction(self, command=None):
        client = None
        try:
            async with asyncio.timeout(30):
                device = bluetooth.async_ble_device_from_address(self.hass, self.address, connectable=True)
                if device is None:
                    raise UpdateFailed('B8X has no connectable Bluetooth advertisement')
                client = await establish_connection(BleakClientWithServiceCache, device,
                    'Flydigi B8X', max_attempts=1, timeout=12)
                return await exchange(client, command)
        finally:
            if client is not None:
                with contextlib.suppress(Exception):
                    await asyncio.wait_for(client.disconnect(), 5)

    async def _run(self, command=None):
        async with self._lock:
            if not self.enabled:
                raise UpdateFailed('B8X Bluetooth access paused')
            self._active = self.hass.async_create_task(self._transaction(command))
            try:
                return await self._active
            except asyncio.CancelledError:
                if not self.enabled:
                    raise UpdateFailed('B8X Bluetooth access paused') from None
                raise
            finally:
                self._active = None

    async def _async_update_data(self):
        try:
            return await self._run()
        except Exception as err:
            raise UpdateFailed(f'B8X read failed: {err}') from err

    async def async_control(self, kind, value):
        try:
            status = await self._run((kind, value))
        except Exception as err:
            raise HomeAssistantError(f'B8X control was not confirmed: {err}') from err
        self.async_set_updated_data(status)

    async def async_pause(self):
        self.enabled = False
        if self._active is not None:
            self._active.cancel()
            await asyncio.gather(self._active, return_exceptions=True)

    async def async_set_enabled(self, enabled):
        if not enabled:
            await self.async_pause()
        else:
            self.enabled = True
        self.hass.config_entries.async_update_entry(self.entry,
            data={**self.entry.data, 'connection_enabled': enabled})
        self.async_update_listeners()
        if enabled:
            await self.async_request_refresh()
