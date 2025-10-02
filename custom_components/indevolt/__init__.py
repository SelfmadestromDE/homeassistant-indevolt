"""Init file for Indevolt Home Assistant integration."""

import logging
import os
import json
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_USERNAME, CONF_PASSWORD, CONF_SCAN_INTERVAL
from homeassistant.helpers.typing import ConfigType

from .client import IndevoltClient
from .coordinator import IndevoltDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

DOMAIN = "indevolt"
PLATFORMS = ["sensor"]

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Indevolt integration (YAML not supported)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Indevolt from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, 8080)
    username = entry.data.get(CONF_USERNAME)
    password = entry.data.get(CONF_PASSWORD)
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, 30)
    model = entry.data.get("device_model", "powerflex2000")

    _LOGGER.debug("Setting up Indevolt entry for host=%s port=%s model=%s", host, port, model)

    # Lade Geräte-Definition (JSON)
    devices_dir = os.path.join(os.path.dirname(__file__), "devices")
    model_file = os.path.join(devices_dir, f"{model}.json")
    try:
        with open(model_file, "r", encoding="utf-8") as f:
            model_config = json.load(f)
    except Exception as e:
        _LOGGER.error("Failed to load device map %s: %s", model_file, e)
        return False

    # Client erstellen
    client = IndevoltClient(hass, host, port, username, password)

    # Coordinator initialisieren
    coordinator = IndevoltDataUpdateCoordinator(hass, client, model_config, scan_interval)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Indevolt config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
