import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_USERNAME, CONF_PASSWORD

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Zusätzliche Felder
CONF_MODEL = "device_model"
CONF_PROTOCOL = "protocol"
CONF_SCAN_INTERVAL = "scan_interval"

DEVICE_MODELS = [
    "powerflex2000",
    "solidflex2000",
    "bk1600",
    "bk1600ultra",
]

PROTOCOLS = ["http", "digest"]


class IndevoltConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Indevolt integration."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            # Wenn Digest → nächster Schritt Credentials
            if user_input[CONF_PROTOCOL] == "digest":
                self._cached_input = user_input
                return await self.async_step_credentials()

            # Direkt speichern
            return self.async_create_entry(
                title=f"Indevolt {user_input[CONF_HOST]}",
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=8080): vol.Coerce(int),
                vol.Required(CONF_MODEL, default="powerflex2000"): vol.In(DEVICE_MODELS),
                vol.Required(CONF_PROTOCOL, default="http"): vol.In(PROTOCOLS),
                vol.Required(CONF_SCAN_INTERVAL, default=30): vol.All(
                    vol.Coerce(int), vol.Range(min=5, max=3600)
                ),
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_credentials(self, user_input=None):
        """Zweiter Schritt: Nur bei Digest Username + Password abfragen."""
        errors = {}

        if user_input is not None:
            final_data = {**self._cached_input, **user_input}
            return self.async_create_entry(
                title=f"Indevolt {final_data[CONF_HOST]}",
                data=final_data,
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )

        return self.async_show_form(step_id="credentials", data_schema=schema, errors=errors)
