import asyncio
import logging
import json
import os
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import IndevoltClient

DOMAIN = "indevolt"
PLATFORMS = ["sensor"]

SCAN_INTERVAL = timedelta(seconds=30)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Indevolt from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    host = entry.data.get("host")
    port = entry.data.get("port", 8080)
    model = entry.data.get("device_model", "powerflex2000")

    _LOGGER.debug(
        "Setting up Indevolt entry for host=%s port=%s model=%s", host, port, model
    )

    client = IndevoltClient(
        hass,
        host,
        port,
        entry.data.get("username"),
        entry.data.get("password"),
    )

    # Lade passende JSON Device-Definition
    device_file = os.path.join(os.path.dirname(__file__), "devices", f"{model}.json")
    device_map = {}
    try:
        with open(device_file, "r", encoding="utf-8") as f:
            device_map = json.load(f)
            _LOGGER.debug("Loaded device map for model %s: %s", model, device_map.keys())
    except Exception as e:
        _LOGGER.error("Failed to load device map %s: %s", device_file, e)

    coordinator = IndevoltDataUpdateCoordinator(hass, client, model)
    coordinator.device_map = device_map
    coordinator.model = model

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload an Indevolt config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


class IndevoltDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator to manage fetching Indevolt data."""

    def __init__(self, hass: HomeAssistant, client: IndevoltClient, model: str):
        super().__init__(
            hass,
            _LOGGER,
            name=f"Indevolt {model}",
            update_interval=SCAN_INTERVAL,
        )
        self.client = client
        self.model = model
        self.device_map = {}  # wird in async_setup_entry gefüllt
        self.entry_id = None  # wird von sensor.py beim Setup gesetzt

    async def _async_update_data(self):
        """Fetch data from Indevolt device."""
        try:
            points = self.device_map.get("read_points", [])
            if not points:
                _LOGGER.warning("No read_points defined for model %s", self.model)
                return {}

            _LOGGER.debug("Fetching points for %s: %s", self.model, points)
            data = await self.client.async_getdata(points)
            _LOGGER.debug("Fetched data for %s: %s", self.model, data)
            return data or {}
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err
