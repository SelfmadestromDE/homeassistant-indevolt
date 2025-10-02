import logging
from homeassistant.components.switch import SwitchEntity
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
        if e.get("platform") == "switch":
            entities.append(IndevoltSwitch(coordinator, client, entry.entry_id, e))

    async_add_entities(entities)

class IndevoltSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, client, entry_id, definition: dict):
        super().__init__(coordinator)
        self._client = client
        self._entry_id = entry_id
        self._key = str(definition["t"])
        self._attr_name = definition.get("name", f"Switch {self._key}")
        self._attr_unique_id = f"indevolt_{entry_id}_{self._key}"

    @property
    def is_on(self):
        return bool(self.coordinator.data.get(self._key, 0))

    async def async_turn_on(self, **kwargs):
        await self._client.async_setdata(int(self._key), [1])
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self._client.async_setdata(int(self._key), [0])
        await self.coordinator.async_request_refresh()
