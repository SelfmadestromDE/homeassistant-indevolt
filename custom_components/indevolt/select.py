import logging
from homeassistant.components.select import SelectEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN, IndevoltDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator: IndevoltDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    for key, meta in coordinator.device_map.get("entities", {}).items():
        if meta.get("platform") != "select":
            continue
        entities.append(
            IndevoltSelect(
                coordinator,
                entry.entry_id,
                key,
                meta.get("name"),
                meta.get("enum"),
            )
        )

    _LOGGER.debug("Adding %d Indevolt selects", len(entities))
    async_add_entities(entities)


class IndevoltSelect(CoordinatorEntity, SelectEntity):
    def __init__(self, coordinator, entry_id, key, name, enum_map):
        super().__init__(coordinator)
        self._key = str(key)
        self._attr_name = name
        self._attr_unique_id = f"indevolt_{entry_id}_{key}"
        self._enum_map = {int(k): v for k, v in enum_map.items()}
        self._reverse_map = {v: k for k, v in self._enum_map.items()}

    @property
    def options(self):
        return list(self._enum_map.values())

    @property
    def current_option(self):
        raw = self.coordinator.data.get(self._key)
        return self._enum_map.get(raw)

    async def async_select_option(self, option: str):
        value = self._reverse_map.get(option)
        if value is None:
            _LOGGER.error("Invalid option %s for %s", option, self._attr_name)
            return
        await self.coordinator.client.async_setdata(int(self._key), [value])
        await self.coordinator.async_request_refresh()
