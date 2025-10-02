import logging
import os
import json
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import IndevoltClient

DOMAIN = "indevolt"
PLATFORMS = ["sensor", "select", "number"]

_LOGGER = logging.getLogger(__name__)


class IndevoltDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Indevolt data."""

    def __init__(self, hass: HomeAssistant, client: IndevoltClient, device_map: dict, scan_interval: int):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.client = client
        self.device_map = device_map
        self.model = device_map.get("model", "unknown")

    async def _async_update_data(self):
        try:
            points = self.device_map.get("read_points", [])
            data = await self.client.async_getdata(points)
            _LOGGER.debug("Coordinator fetched data: %s", data)
            return data
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Indevolt integration from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    host = entry.data["host"]
    port = entry.data.get("port", 8080)
    username = entry.data.get("username")
    password = entry.data.get("password")
    model = entry.data.get("device_model", "powerflex2000")
    scan_interval = entry.data.get("scan_interval", 30)

    # Lade Gerätemap
    dev_path = os.path.join(os.path.dirname(__file__), "devices", f"{model}.json")
    try:
        with open(dev_path, "r", encoding="utf-8") as f:
            device_map = json.load(f)
    except Exception as e:
        _LOGGER.error("Failed to load device map %s: %s", dev_path, e)
        device_map = {"model": model, "read_points": [], "entities": {}}

    client = IndevoltClient(hass, host, port, username, password)
    coordinator = IndevoltDataUpdateCoordinator(hass, client, device_map, scan_interval)

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
