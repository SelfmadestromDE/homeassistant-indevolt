import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN, IndevoltDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Indevolt switches from config entry."""
    coordinator: IndevoltDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    for key, meta in coordinator.device_map.get("entities", {}).items():
        if meta.get("enum") and set(meta["enum"].values()) == {"ON", "OFF"}:
            entities.append(
                IndevoltSwitch(
                    coordinator,
                    entry.entry_id,
                    key,
                    meta.get("name"),
                )
            )

    _LOGGER.debug("Adding %d Indevolt switches", len(entities))
    async_add_entities(entities)


class IndevoltSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of an Indevolt switch."""

    def __init__(self, coordinator, entry_id, key, name):
        super().__init__(coordinator)
        self._key = str(key)
        self._attr_name = name
        self._attr_unique_id = f"indevolt_{entry_id}_switch_{key}"

    @property
    def is_on(self):
        return self.coordinator.data.get(self._key) in ["1", 1, "ON", "1000"]

    async def async_turn_on(self, **kwargs):
        await self.coordinator.client.async_setdata(int(self._key), [1])
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self.coordinator.client.async_setdata(int(self._key), [0])
        await self.coordinator.async_request_refresh()
