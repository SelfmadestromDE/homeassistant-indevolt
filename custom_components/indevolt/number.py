import logging
from homeassistant.components.number import NumberEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN, IndevoltDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator: IndevoltDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    device_map = coordinator.device_map.get("entities", {})

    for key, meta in device_map.items():
        if meta.get("writable") and not meta.get("enum"):
            entities.append(
                IndevoltNumber(
                    coordinator,
                    entry.entry_id,
                    key,
                    meta.get("name"),
                    meta.get("unit"),
                    meta.get("min", 0),
                    meta.get("max", 100),
                    meta.get("step", 1),
                )
            )

    async_add_entities(entities)

class IndevoltNumber(CoordinatorEntity, NumberEntity):
    def __init__(self, coordinator, entry_id, key, name, unit, min_v, max_v, step):
        super().__init__(coordinator)
        self._key = str(key)
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_unique_id = f"indevolt_{entry_id}_{key}"
        self._attr_native_min_value = min_v
        self._attr_native_max_value = max_v
        self._attr_native_step = step

    @property
    def native_value(self):
        return self.coordinator.data.get(self._key)

    async def async_set_native_value(self, value: float):
        await self.coordinator.client.async_setdata(int(self._key), [value])
        await self.coordinator.async_request_refresh()
