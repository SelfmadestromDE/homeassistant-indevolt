import logging
from homeassistant.components.select import SelectEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN, IndevoltDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator: IndevoltDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    device_map = coordinator.device_map.get("entities", {})

    for key, meta in device_map.items():
        if meta.get("writable") and meta.get("enum"):
            entities.append(
                IndevoltSelect(
                    coordinator,
                    entry.entry_id,
                    key,
                    meta.get("name"),
                    meta.get("enum"),
                )
            )

    async_add_entities(entities)

class IndevoltSelect(CoordinatorEntity, SelectEntity):
    def __init__(self, coordinator, entry_id, key, name, enum_map):
        super().__init__(coordinator)
        self._key = str(key)
        self._attr_name = name
        self._attr_unique_id = f"indevolt_{entry_id}_{key}"
        self._enum_map = enum_map
        self._attr_options = list(enum_map.values())

    @property
    def current_option(self):
        raw = self.coordinator.data.get(self._key)
        return self._enum_map.get(str(raw))

    async def async_select_option(self, option: str):
        reverse_map = {v: int(k) for k, v in self._enum_map.items()}
        value = reverse_map.get(option)
        if value is not None:
            await self.coordinator.client.async_setdata(int(self._key), [value])
            await self.coordinator.async_request_refresh()
