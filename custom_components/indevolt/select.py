import logging
from homeassistant.components.select import SelectEntity
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
        if e.get("platform") == "select":
            entities.append(IndevoltSelect(coordinator, client, entry.entry_id, e))

    async_add_entities(entities)

class IndevoltSelect(CoordinatorEntity, SelectEntity):
    def __init__(self, coordinator, client, entry_id, definition: dict):
        super().__init__(coordinator)
        self._client = client
        self._entry_id = entry_id
        self._key = str(definition["t"])
        self._options = definition.get("options", [])
        self._attr_name = definition.get("name", f"Select {self._key}")
        self._attr_unique_id = f"indevolt_{entry_id}_{self._key}"
        self._attr_options = self._options

    @property
    def current_option(self):
        val = self.coordinator.data.get(self._key)
        if val is None:
            return None
        try:
            return self._options[val]
        except Exception:
            return str(val)

    async def async_select_option(self, option: str):
        if option in self._options:
            idx = self._options.index(option)
            await self._client.async_setdata(int(self._key), [idx])
            await self.coordinator.async_request_refresh()
