# custom_components/indevolt/__init__.py
import logging
from datetime import timedelta
import json, os

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import IndevoltClient

_LOGGER = logging.getLogger(__name__)
DOMAIN = "indevolt"

PLATFORMS = ["sensor", "switch", "number", "select", "button"]


class IndevoltCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, client: IndevoltClient, read_points: list[int]):
        super().__init__(hass, _LOGGER, name="indevolt", update_interval=timedelta(seconds=30))
        self.client = client
        self.read_points = read_points

    async def _async_update_data(self):
        try:
            return await self.client.async_getdata(self.read_points)
        except Exception as err:
            raise UpdateFailed(err) from err


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    host = entry.data["host"]
    model = entry.data.get("model")
    username = entry.data.get("username")
    password = entry.data.get("password")

    client = IndevoltClient(hass, host, username=username, password=password)

    # load device map
    base_path = os.path.dirname(__file__)
    device_file = os.path.join(base_path, "devices", f"{model.lower()}.json")
    try:
        with open(device_file, "r", encoding="utf-8") as f:
            device_map = json.load(f)
    except FileNotFoundError:
        _LOGGER.warning("No device map for %s, using minimal", model)
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
