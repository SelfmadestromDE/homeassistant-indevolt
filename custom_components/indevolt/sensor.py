import logging
from homeassistant.components.sensor import SensorEntity
from .coordinator import IndevoltDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# Mapping-Tabellen für Enums
ENUM_MAPPINGS = {
    "6001": {1000: "Static", 1001: "Charging", 1002: "Discharging"},
    "7101": {1: "Self-consumed prioritized", 5: "Charge/Discharge Schedule"},
    "7120": {1000: "ON", 1001: "OFF"},
    "47005": {1: "Self-consumed prioritized", 2: "Charge/Discharge Schedule", 4: "Real-time Control"},
    "47015": {0: "Standby", 1: "Charging", 2: "Discharging"},
}

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Indevolt sensors dynamically from model JSON."""
    coordinator: IndevoltDataUpdateCoordinator = hass.data["indevolt"][entry.entry_id]

    model_config = coordinator.model_config
    entities = []

    if "entities" in model_config:
        # Dynamisch aus JSON bauen
        for key, meta in model_config["entities"].items():
            entities.append(
                IndevoltSensor(
                    coordinator,
                    str(key),
                    meta.get("name", f"Sensor {key}"),
                    meta.get("unit")
                )
            )
    else:
        # Fallback (falls nur read_points definiert sind)
        for key in model_config.get("read_points", []):
            entities.append(
                IndevoltSensor(coordinator, str(key), f"Sensor {key}", None)
            )

    _LOGGER.debug("Adding %s Indevolt sensors for model %s", len(entities), model_config.get("model"))
    async_add_entities(entities)


class IndevoltSensor(SensorEntity):
    """Representation of an Indevolt sensor."""

    def __init__(self, coordinator, key, name, unit):
        self.coordinator = coordinator
        self._key = key
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_unique_id = f"indevolt_{coordinator.entry_id}_{key}"

    @property
    def native_value(self):
        """Return the value of the sensor, applying enum mapping if needed."""
        val = self.coordinator.data.get(self._key)

        if val is None:
            return None

        # Enum-Mapping anwenden, falls vorhanden
        if self._key in ENUM_MAPPINGS:
            mapped = ENUM_MAPPINGS[self._key].get(val, val)
            _LOGGER.debug("Sensor %s (%s) mapped value: %s -> %s", self._key, self._attr_name, val, mapped)
            return mapped

        _LOGGER.debug("Sensor %s (%s) raw value: %s", self._key, self._attr_name, val)
        return val

    @property
    def available(self) -> bool:
        return self._key in self.coordinator.data

    async def async_update(self):
        """Update via coordinator."""
        await self.coordinator.async_request_refresh()
