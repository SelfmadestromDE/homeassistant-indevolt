import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import IndevoltDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# Enum mappings für lesbare Werte
ENUM_MAPPINGS = {
    "7101": {
        1: "Self-consumed prioritized",
        5: "Charge/Discharge Schedule"
    },
    "6001": {
        1000: "Idle",
        1001: "Charging",
        1002: "Discharging"
    },
    "7120": {
        1000: "ON",
        1001: "OFF"
    },
    "47005": {
        1: "Self-consumed prioritized",
        2: "Charge/Discharge Schedule",
        4: "Real-time Control"
    },
    "47015": {
        0: "Standby",
        1: "Charging",
        2: "Discharging"
    }
}

# Optional: Icons je nach Enum-Status
ENUM_ICONS = {
    "6001": {
        1000: "mdi:battery",
        1001: "mdi:battery-arrow-up",
        1002: "mdi:battery-arrow-down"
    },
    "7120": {
        1000: "mdi:lan-connect",
        1001: "mdi:lan-disconnect"
    },
    "47015": {
        0: "mdi:power-standby",
        1: "mdi:battery-arrow-up",
        2: "mdi:battery-arrow-down"
    }
}


async def async_setup_entry(hass, entry, async_add_entities):
    """Setup Indevolt sensors."""
    coordinator: IndevoltDataUpdateCoordinator = hass.data["indevolt"][entry.entry_id]

    sensors = []
    device_map = coordinator.device_map.get("entities", {})

    for key, meta in device_map.items():
        sensors.append(
            IndevoltSensor(
                coordinator,
                entry.entry_id,
                key,
                meta.get("name"),
                meta.get("unit"),
                meta.get("icon"),
            )
        )

    async_add_entities(sensors)
    _LOGGER.debug("Added %s Indevolt sensors for model %s", len(sensors), coordinator.model)


class IndevoltSensor(CoordinatorEntity, SensorEntity):
    """Representation of an Indevolt sensor."""

    def __init__(self, coordinator, entry_id, key, name, unit, icon):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name or f"Indevolt {key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._attr_unique_id = f"indevolt_{entry_id}_{key}"

    @property
    def native_value(self):
        value = self.coordinator.data.get(self._key)

        # Enum-Mapping
        if self._key in ENUM_MAPPINGS and value in ENUM_MAPPINGS[self._key]:
            return ENUM_MAPPINGS[self._key][value]

        return value

    @property
    def icon(self):
        value = self.coordinator.data.get(self._key)

        # Icon abhängig vom Enum-Wert
        if self._key in ENUM_ICONS and value in ENUM_ICONS[self._key]:
            return ENUM_ICONS[self._key][value]

        return self._attr_icon
