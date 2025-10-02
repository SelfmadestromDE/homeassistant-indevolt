import logging
import os
import json
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .client import IndevoltClient

DOMAIN = "indevolt"
PLATFORMS = ["sensor", "select", "switch", "number"]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Indevolt from a config entry."""
    host = entry.data["host"]
    port = entry.data.get("port", 8080)
    model = entry.data.get("model", "powerflex2000")

    _LOGGER.debug("Setting up Indevolt entry for host=%s port=%s model=%s", host, port, model)

    # Lade Geräte-Mapping
    device_map = await hass.async_add_executor_job(load_device_map, model)
    if not device_map:
        _LOGGER.error("Failed to load device map for model %s", model)
        return False

    client = IndevoltClient(host, port)

    coordinator = IndevoltDataUpdateCoordinator(hass, client, device_map, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload Indevolt entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


def load_device_map(model: str):
    """Lade Geräte-Mapping aus JSON-Datei."""
    path = os.path.join(os.path.dirname(__file__), "devices", f"{model}.json")
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        _LOGGER.error("Error reading JSON file %s: %s", path, e)
        return None


class IndevoltDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Indevolt data."""

    def __init__(self, hass, client, device_map, entry):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
        )
        self.client = client
        self.device_map = device_map
        self.entry = entry

    async def _async_update_data(self):
        read_points = self.device_map.get("read_points", [])
        if not read_points:
            _LOGGER.warning("No read_points defined in device map")
            return {}

        _LOGGER.debug("Fetching Indevolt data for points: %s", read_points)
        data = await self.client.async_getdata(read_points)
        _LOGGER.debug("Coordinator fetched data: %s", data)
        return data
