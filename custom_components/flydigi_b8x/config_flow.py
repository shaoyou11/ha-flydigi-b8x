"""Explicit address configuration, no pairing or device reset."""
import re
import voluptuous as vol
from homeassistant import config_entries


class B8XConfigFlow(config_entries.ConfigFlow, domain='flydigi_b8x'):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            address = user_input['address'].strip().upper()
            if not re.fullmatch(r'(?:[0-9A-F]{2}:){5}[0-9A-F]{2}', address):
                errors['address'] = 'invalid_address'
            else:
                await self.async_set_unique_id(address)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title='Flydigi B8X', data={
                    'address': address, 'connection_enabled': True})
        return self.async_show_form(step_id='user', data_schema=vol.Schema({
            vol.Required('address'): str}), errors=errors)
