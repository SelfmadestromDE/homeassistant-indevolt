import logging
import json
import os
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .client import IndevoltClient

DOMAIN = "indevolt"
PLATFORMS = ["sensor", "select", "number"]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Indevolt from a config entry."""
    host = entry.data["host"]
    port = entry.data.get("port", 8080)
    model = entry.data.get("model", "powerflex2000")
    scan_interval = entry.data.get("scan_interval", 30)

    _LOGGER.debug(
        "Setting up Indevolt entry for host=%s port=%s model=%s scan_interval=%s",
        host,
        port,
        model,
        scan_interval,
    )

    client = IndevoltClient(hass, host, port)

    # Device Map laden
    devices_path = os.path.join(os.path.dirname(__file__), "devices")
    model_file = os.path.join(devices_path, f"{model}.json")

    try:
        with open(model_file, "r") as f:
            device_map = json.load(f)
    except Exception as e:
        _LOGGER.error("Failed to load device map %s: %s", model_file, e)
        return False

    coordinator = IndevoltDataUpdateCoordinator(
        hass,
        client,
        model,
        device_map,
        scan_interval,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload Indevolt config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


class IndevoltDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from Indevolt device."""

    def __init__(self, hass, client, model, device_map, scan_interval):
        super().__init__(
            hass,
            _LOGGER,
            name=f"Indevolt {model}",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.client = client
        self.model = model
        self.device_map = device_map
        self.entry_id = None  # wird später vom Setup gesetzt

    async def _async_update_data(self):
        read_points = self.device_map.get("read_points", [])
        if not read_points:
            _LOGGER.warning("No read_points defined for model %s", self.model)
            return {}

        try:
            result = await self.client.async_getdata(read_points)
            _LOGGER.debug("Coordinator fetched data: %s", result)
            return result
        except Exception as e:
            _LOGGER.error("Error fetching Indevolt data: %s", e)
            return {}
