import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_USERNAME, CONF_PASSWORD
import homeassistant.helpers.config_validation as cv

from . import DOMAIN

DEVICE_MODELS = [
    "powerflex2000",
    "solidflex200",
    "bk1600",
    "bk1600ultra"
]

DEFAULT_PORT = 8080


class IndevoltConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            # hier könnte man optional eine Testverbindung zum Gerät machen
            return self.async_create_entry(
                title=f"Indevolt {user_input[CONF_HOST]}",
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Required("device_model"): vol.In(DEVICE_MODELS),
                vol.Optional(CONF_USERNAME): str,
                vol.Optional(CONF_PASSWORD): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
