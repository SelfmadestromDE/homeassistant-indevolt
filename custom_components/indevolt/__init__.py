import asyncio
import logging
import os
import json
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.exceptions import ConfigEntryNotReady

from .client import IndevoltClient

DOMAIN = "indevolt"
PLATFORMS = ["sensor", "select", "number"]

_LOGGER = logging.getLogger(__name__)

CONF_MODEL = "device_model"
CONF_SCAN_INTERVAL = "scan_interval"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Indevolt from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    host = entry.data["host"]
    port = entry.data["port"]
    model = entry.data[CONF_MODEL]
    protocol = entry.data.get("protocol", "http")
    username = entry.data.get("username")
    password = entry.data.get("password")
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, 30)

    _LOGGER.debug(
        "Setting up Indevolt entry for host=%s port=%s model=%s scan_interval=%s",
        host,
        port,
        model,
        scan_interval,
    )

    # JSON-Device Map laden
    device_map = await hass.async_add_executor_job(_load_device_map, model)

    if not device_map:
        raise ConfigEntryNotReady(f"Device map for {model} not found or invalid")

    client = IndevoltClient(
        hass,
        host=host,
        port=port,
        username=username,
        password=password,
    )

    coordinator = IndevoltDataUpdateCoordinator(
        hass,
        client=client,
        model=model,
        device_map=device_map,
        update_interval=timedelta(seconds=scan_interval),
    )

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
    """Coordinator für Indevolt Datenabfrage."""

    def __init__(self, hass, client, model, device_map, update_interval):
        super().__init__(
            hass,
            _LOGGER,
            name=f"Indevolt {model}",
            update_interval=update_interval,
        )
        self.client = client
        self.model = model
        self.device_map = device_map
        self.entry_id = None  # wird im async_setup_entry nicht zwingend gebraucht

    async def _async_update_data(self):
        try:
            read_points = self.device_map.get("read_points", [])
            if not read_points:
                return {}
            data = await self.client.async_getdata(read_points)
            _LOGGER.debug("Coordinator fetched data: %s", data)
            return data
        except Exception as err:
            _LOGGER.error("Error updating Indevolt data: %s", err)
            return {}


def _load_device_map(model: str) -> dict:
    base_path = os.path.dirname(__file__)
    devices_dir = os.path.join(base_path, "devices")
    file_path = os.path.join(devices_dir, f"{model}.json")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        _LOGGER.error("Error reading JSON file %s: %s", file_path, e)
        return {}
