import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Indevolt sensors dynamically from device_map (JSON)."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    device_map = data["device_map"]

    read_points = device_map.get("read_points", [])
    entities = []

    for point in read_points:
        # Versuche Mapping aus JSON (entities) zu finden
        definition = None
        if "entities" in device_map:
            definition = next((e for e in device_map["entities"] if str(e.get("t")) == str(point)), None)

        if definition:
            name = definition.get("name", f"Register {point}")
            unit = definition.get("unit")
        else:
            name = f"Register {point}"
            unit = None

        entities.append(
            IndevoltSensor(coordinator, entry.entry_id, str(point), name, unit)
        )

    _LOGGER.debug(
        "Adding %d Indevolt sensors for model %s",
        len(entities),
        device_map.get("model"),
    )
    async_add_entities(entities)


class IndevoltSensor(CoordinatorEntity, SensorEntity):
    """Representation of an Indevolt sensor."""

    def __init__(self, coordinator, entry_id: str, key: str, name: str, unit: str | None):
        super().__init__(coordinator)
        self._key = key
        self._entry_id = entry_id
        self._attr_name = name
        self._attr_unique_id = f"indevolt_{entry_id}_{key}"
        self._attr_native_unit_of_measurement = unit

    @property
    def native_value(self):
        val = self.coordinator.data.get(self._key)
        _LOGGER.debug(
            "Sensor %s (%s) via entry %s -> %s",
            self._key,
            self._attr_name,
            self._entry_id,
            val,
        )
        return val
