import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_USERNAME, CONF_PASSWORD

from . import DOMAIN

DEVICE_MODELS = [
    "powerflex2000",
    "solidflex2000",
    "bk1600",
    "bk1600ultra"
]

DEFAULT_PORT = 8080
CONF_PROTOCOL = "protocol"


class IndevoltConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Erster Schritt: Host, Port, Modell, Protokoll."""
        errors = {}

        if user_input is not None:
            protocol = user_input[CONF_PROTOCOL]

            # Digest gewählt -> Username/Password im nächsten Schritt
            if protocol == "http_digest":
                self._cached_input = user_input
                return await self.async_step_credentials()

            # HTTP ohne Auth -> direkt Entry erstellen
            return self.async_create_entry(
                title=f"Indevolt {user_input[CONF_HOST]}",
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Required("device_model"): vol.In(DEVICE_MODELS),
                vol.Required(CONF_PROTOCOL, default="http"): vol.In(["http", "http_digest"]),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_credentials(self, user_input=None):
        """Zweiter Schritt: Nur bei Digest Username + Password abfragen."""
        errors = {}
        if user_input is not None:
            # Host/Port/Model/Protocol aus Step 1 + Credentials zusammenführen
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
