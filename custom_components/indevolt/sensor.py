import logging
from homeassistant.components.sensor import SensorEntity
from . import IndevoltDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


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
        val = self.coordinator.data.get(self._key)
        _LOGGER.debug("Sensor %s (%s) -> %s", self._key, self._attr_name, val)
        return val

    @property
    def available(self) -> bool:
        return self._key in self.coordinator.data

    async def async_update(self):
        """Update via coordinator."""
        await self.coordinator.async_request_refresh()
