import logging
from homeassistant.core import HomeAssistant
from homeassistant.helpers import discovery
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.components import select, number, button
from homeassistant.const import CONF_HOST, CONF_PORT

from .client import IndevoltClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the Indevolt integration from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    
    client = IndevoltClient(hass, host, port)
    
    # Define coordinator and initialize it
    coordinator = IndevoltDataUpdateCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()

    # Add Grid Charge entities
    async_add_entities([
        GridChargeMode(coordinator, entry.entry_id),
        GridChargePower(coordinator, entry.entry_id),
        GridChargeSOC(coordinator, entry.entry_id),
        ApplyGridChargeButton(coordinator, entry.entry_id)
    ])
    
    # Register coordinator for the entry
    hass.data[DOMAIN][entry.entry_id] = coordinator

class IndevoltDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the Indevolt device."""

    def __init__(self, hass, client):
        """Initialize the data coordinator."""
        self.client = client
        self.model = "powerflex2000"
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=60))

    async def _async_update_data(self):
        """Fetch the data from the Indevolt API."""
        try:
            data = await self.client.async_getdata([1664, 1665, 1501, 1502, 2108, 6000, 6001, 6002])
            return data
        except Exception as e:
            _LOGGER.error(f"Error fetching data: {e}")
            return {}
