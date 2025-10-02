# custom_components/indevolt/number.py
from homeassistant.components.number import NumberEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from . import DOMAIN

class IndevoltNumber(CoordinatorEntity, NumberEntity):
    def __init__(self, coordinator, client, name, key, t_register, min_v, max_v, step=1):
        super().__init__(coordinator)
        self.client = client
        self._attr_name = name
        self._key = str(key)
        self._t = t_register
        self._attr_native_min_value = min_v
        self._attr_native_max_value = max_v
        self._attr_native_step = step

    @property
    def native_value(self):
        val = self.coordinator.data.get(self._key)
        return val

    async def async_set_native_value(self, value: float):
        await self.client.async_setdata(self._t, [int(value)])
        await self.coordinator.async_request_refresh()

async def async_setup_entry(hass, entry, async_add_entities):
    inst = hass.data[DOMAIN][entry.entry_id]
    coord = inst["coordinator"]
    client = inst["client"]

    entities = [
        IndevoltNumber(coord, client, "Target SOC", 47017, 47017, 0, 100, 1),
        IndevoltNumber(coord, client, "Target Power", 47016, 47016, 0, 1200, 10),
    ]
    async_add_entities(entities, True)
