import logging
from homeassistant.components.number import NumberEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN, IndevoltDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Indevolt numbers from config entry."""
    coordinator: IndevoltDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    for key, meta in coordinator.device_map.get("entities", {}).items():
        if key in ["47016", "47017"]:
            min_v = 0
            max_v = 100 if key == "47017" else 1200
            entities.append(
                IndevoltNumber(
                    coordinator,
                    entry.entry_id,
                    key,
                    meta.get("name"),
                    meta.get("unit"),
                    min_v,
                    max_v,
                )
            )

    _LOGGER.debug("Adding %d Indevolt numbers", len(entities))
    async_add_entities(entities)


class IndevoltNumber(CoordinatorEntity, NumberEntity):
    """Representation of an Indevolt number entity."""

    def __init__(self, coordinator, entry_id, key, name, unit, min_value, max_value):
        super().__init__(coordinator)
        self._key = str(key)
        self._attr_name = name
        self._attr_unique_id = f"indevolt_{entry_id}_number_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value

    @property
    def native_value(self):
        return self.coordinator.data.get(self._key)

    async def async_set_native_value(self, value: float):
        await self.coordinator.client.async_setdata(int(self._key), [int(value)])
        await self.coordinator.async_request_refresh()
