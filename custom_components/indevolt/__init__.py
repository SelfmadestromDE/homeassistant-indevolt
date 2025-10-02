import logging
import os
import json
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import IndevoltClient

_LOGGER = logging.getLogger(__name__)
DOMAIN = "indevolt"

PLATFORMS = ["sensor", "switch", "number", "select", "button"]


class IndevoltCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, client: IndevoltClient, read_points: list[int]):
        super().__init__(
            hass,
            _LOGGER,
            name="indevolt",
            update_interval=timedelta(seconds=30),
        )
        self.client = client
        self.read_points = read_points

    async def _async_update_data(self):
        try:
            return await self.client.async_getdata(self.read_points)
        except Exception as err:
            raise UpdateFailed(err) from err


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Indevolt integration from a config entry."""
    host = entry.data["host"]
    port = entry.data.get("port", 8080)
    model = entry.data.get("device_model", "").lower()
    protocol = entry.data.get("protocol", "http")
    username = entry.data.get("username")
    password = entry.data.get("password")

    # Nur bei Digest Username/Passwort weiterreichen
    if protocol == "http_digest":
        client = IndevoltClient(hass, host, port=port, username=username, password=password)
    else:
        client = IndevoltClient(hass, host, port=port)

    # Lade JSON
    base_path = os.path.dirname(__file__)
    device_file = os.path.join(base_path, "devices", f"{model}.json")

    if not os.path.exists(device_file):
        _LOGGER.warning("No device map for model '%s'. Using default minimal read points.", model)
        device_map = {"read_points": [1664, 1665], "entities": []}
    else:
        try:
            with open(device_file, "r", encoding="utf-8") as f:
                device_map = json.load(f)
        except Exception as e:
            _LOGGER.error("Failed to load device map %s: %s", device_file, e)
            device_map = {"read_points": [1664, 1665], "entities": []}

    coordinator = IndevoltCoordinator(hass, client, device_map.get("read_points", []))
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "client": client,
        "device_map": device_map,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
