# custom_components/indevolt/button.py
from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from . import DOMAIN

class IndevoltButton(CoordinatorEntity, ButtonEntity):
    def __init__(self, coordinator, client, name, action):
        super().__init__(coordinator)
        self.client = client
        self._attr_name = name
        self._action = action

    async def async_press(self) -> None:
        await self._action()
        await self.coordinator.async_request_refresh()

async def async_setup_entry(hass, entry, async_add_entities):
    inst = hass.data[DOMAIN][entry.entry_id]
    coord = inst["coordinator"]
    client = inst["client"]

    async_add_entities([
        IndevoltButton(coord, client, "Start Real-time Control", lambda: client.async_set_mode(4))
    ], True)
