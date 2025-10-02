# custom_components/indevolt/select.py
from homeassistant.components.select import SelectEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from . import DOMAIN

class IndevoltModeSelect(CoordinatorEntity, SelectEntity):
    def __init__(self, coordinator, client):
        super().__init__(coordinator)
        self.client = client
        self._attr_name = "Indevolt Mode"
        self._options_map = {
            "Self-consumed": 1,
            "Schedule": 2,
            "Real-time": 4
        }

    @property
    def options(self):
        return list(self._options_map.keys())

    @property
    def current_option(self):
        val = self.coordinator.data.get("47005")
        for label, code in self._options_map.items():
            if code == val:
                return label
        return None

    async def async_select_option(self, option: str):
        code = self._options_map.get(option)
        if code is not None:
            await self.client.async_set_mode(code)
            await self.coordinator.async_request_refresh()

async def async_setup_entry(hass, entry, async_add_entities):
    inst = hass.data[DOMAIN][entry.entry_id]
    coord = inst["coordinator"]
    client = inst["client"]
    async_add_entities([IndevoltModeSelect(coord, client)], True)
