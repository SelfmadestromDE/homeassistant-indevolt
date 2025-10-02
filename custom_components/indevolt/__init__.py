import logging
import os
import json
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .client import IndevoltClient

DOMAIN = "indevolt"
PLATFORMS = ["sensor", "select", "number"]

SCAN_INTERVAL = timedelta(seconds=30)

_LOGGER = logging.getLogger(__name__)


class IndevoltDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Indevolt data."""

    def __init__(self, hass: HomeAssistant, client: IndevoltClient, host: str, model: str, device_map: dict):
        super().__init__(
            hass,
            _LOGGER,
            name=f"Indevolt ({host})",
            update_interval=SCAN_INTERVAL,
        )
        self.client = client
        self.host = host
        self.model = model
        self.device_map = device_map
        self.data = {}

    async def _async_update_data(self):
        """Fetch data from Indevolt device."""
        try:
            points = self.device_map.get("read_points", [])
            if not points:
                _LOGGER.warning("No read_points defined for model %s", self.model)
                return {}

            _LOGGER.debug("Fetching Indevolt data points: %s", points)
            result = await self.client.async_getdata(points)
            _LOGGER.debug("Fetched data: %s", result)
            return result or {}
        except Exception as e:
            _LOGGER.error("Failed to fetch Indevolt data: %s", e)
            return {}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Indevolt integration from a config entry."""
    host = entry.data.get("host")
    port = entry.data.get("port", 8080)
    username = entry.data.get("username")
    password = entry.data.get("password")
    model = entry.data.get("model", "powerflex2000")

    _LOGGER.debug("Setting up Indevolt entry for host=%s port=%s model=%s", host, port, model)

    # Lade Gerätebeschreibung
    device_map = {}
    try:
        devices_dir = os.path.join(os.path.dirname(__file__), "devices")
        json_path = os.path.join(devices_dir, f"{model}.json")
        with open(json_path, "r", encoding="utf-8") as f:
            device_map = json.load(f)
        _LOGGER.debug("Loaded device map for model %s: %s", model, json_path)
    except Exception as e:
        _LOGGER.error("Failed to load device map %s: %s", model, e)

    # API-Client
    client = IndevoltClient(hass, host, port, username, password)

    # Coordinator
    coordinator = IndevoltDataUpdateCoordinator(hass, client, host, model, device_map)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Plattformen laden (sensor, select, number)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload Indevolt config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
