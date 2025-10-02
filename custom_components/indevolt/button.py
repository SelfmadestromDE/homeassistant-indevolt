import logging
from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    client = data["client"]
    device_map = data["device_map"]

    entities = []
    for e in device_map.get("entities", []):
        if e.get("platform") == "button":
            entities.append(IndevoltButton(coordinator, client, entry.entry_id, e))

    async_add_entities(entities)

class IndevoltButton(CoordinatorEntity, ButtonEntity):
    def __init__(self, coordinator, client, entry_id, definition: dict):
        super().__init__(coordinator)
        self._client = client
        self._entry_id = entry_id
        self._key = str(definition["t"])
        self._action = definition.get("action")
        self._attr_name = definition.get("name", f"Button {self._key}")
        self._attr_unique_id = f"indevolt_{entry_id}_{self._key}"

    async def async_press(self):
        if self._action:
            f = self._action.get("f", 16)
            t = self._action.get("t", int(self._key))
            v = self._action.get("v", [1])
            await self._client.async_setdata(t, v)
            await self.coordinator.async_request_refresh()
