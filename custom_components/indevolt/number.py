import logging
from homeassistant.components.number import NumberEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN, IndevoltDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# Welche Keys als Number steuerbar sind
NUMBER_CONFIG = {
    "47016": {"name": "Target Power", "unit": "W", "min": -1200, "max": 1200, "step": 1},
    "47017": {"name": "Target SOC", "unit": "%", "min": 0, "max": 100, "step": 1},
}


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Indevolt numbers from config entry."""
    coordinator: IndevoltDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    for key, config in NUMBER_CONFIG.items():
        entities.append(
            IndevoltNumber(
                coordinator,
                entry.entry_id,
                key,
                config["name"],
                config["unit"],
                config["min"],
                config["max"],
                config["step"],
            )
        )

    _LOGGER.debug(
        "Adding %d Indevolt numbers for model %s", len(entities), coordinator.model
    )
    async_add_entities(entities)


class IndevoltNumber(CoordinatorEntity, NumberEntity):
    """Representation of an Indevolt number."""

    def __init__(self, coordinator, entry_id, key, name, unit, min_value, max_value, step):
        super().__init__(coordinator)
        self._key = str(key)
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_unique_id = f"indevolt_{entry_id}_{key}"
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = step

    @property
    def native_value(self):
        return self.coordinator.data.get(self._key)

    async def async_set_native_value(self, value: float):
        """Send new value to device."""
        _LOGGER.debug("Setting %s (%s) to %s", self._attr_name, self._key, value)
        await self.coordinator.client.async_setdata(self._key, value)
        await self.coordinator.async_request_refresh()
