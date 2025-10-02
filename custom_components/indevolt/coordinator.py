import logging
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .client import IndevoltClient

_LOGGER = logging.getLogger(__name__)

class IndevoltDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator to manage Indevolt data fetching."""

    def __init__(self, hass, client: IndevoltClient, model_config: dict, scan_interval: int = 30):
        super().__init__(
            hass,
            _LOGGER,
            name="indevolt",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.client = client
        self.model_config = model_config

    async def _async_update_data(self):
        """Fetch data from Indevolt device."""
        points = self.model_config.get("read_points", [])
        if not points:
            return {}
        try:
            data = await self.client.async_getdata(points)
            _LOGGER.debug("Coordinator fetched data: %s", data)
            return data
        except Exception as e:
            _LOGGER.error("Error updating Indevolt data: %s", e)
            return {}
