import logging
from homeassistant.components.number import NumberEntity
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
        if e.get("platform") == "number":
            entities.append(IndevoltNumber(coordinator, client, entry.entry_id, e))

    async_add_entities(entities)

class IndevoltNumber(CoordinatorEntity, NumberEntity):
    def __init__(self, coordinator, client, entry_id, definition: dict):
        super().__init__(coordinator)
        self._client = client
        self._entry_id = entry_id
        self._key = str(definition["t"])
        self._attr_name = definition.get("name", f"Number {self._key}")
        self._attr_unique_id = f"indevolt_{entry_id}_{self._key}"
        self._attr_native_min_value = definition.get("min", 0)
        self._attr_native_max_value = definition.get("max", 100)
        self._attr_native_step = definition.get("step", 1)
        self._attr_native_unit_of_measurement = definition.get("unit")

    @property
    def native_value(self):
        return self.coordinator.data.get(self._key)

    async def async_set_native_value(self, value: float):
        await self._client.async_setdata(int(self._key), [value])
        await self.coordinator.async_request_refresh()
