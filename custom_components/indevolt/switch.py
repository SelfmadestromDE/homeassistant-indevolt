# custom_components/indevolt/switch.py
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from . import DOMAIN

class IndevoltSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, client, name, key, state_value):
        super().__init__(coordinator)
        self.client = client
        self._attr_name = name
        self._key = str(key)
        self._state_value = state_value

    @property
    def is_on(self):
        return self.coordinator.data.get(self._key) == self._state_value

    async def async_turn_on(self, **kwargs):
        await self.client.async_setdata(47015, [self._state_value, 0, 0])
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self.client.async_setdata(47015, [0, 0, 0])
        await self.coordinator.async_request_refresh()

async def async_setup_entry(hass, entry, async_add_entities):
    inst = hass.data[DOMAIN][entry.entry_id]
    coord = inst["coordinator"]
    client = inst["client"]

    entities = [
        IndevoltSwitch(coord, client, "Force Charge", 47015, 1),
        IndevoltSwitch(coord, client, "Force Discharge", 47015, 2),
    ]
    async_add_entities(entities, True)
