import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN, IndevoltDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# Standard-Icons für verschiedene Kategorien
ICON_MAP = {
    "Battery SOC": "mdi:battery",
    "Battery State": "mdi:battery-heart-variant",
    "Battery Power": "mdi:flash",
    "Battery Daily Charging Energy": "mdi:battery-plus",
    "Battery Daily Discharging Energy": "mdi:battery-minus",
    "Battery Total Charging Energy": "mdi:battery-plus-outline",
    "Battery Total Discharging Energy": "mdi:battery-minus-outline",
    "Daily Production": "mdi:solar-power",
    "Cumulative Production": "mdi:chart-line",
    "Total DC Output Power": "mdi:current-dc",
    "Total AC Output Power": "mdi:current-ac",
    "Total AC Input Power": "mdi:transmission-tower-import",
    "Total AC Input Energy": "mdi:transmission-tower",
    "Rated Capacity": "mdi:battery-high",
    "Working Mode": "mdi:factory",
    "Control Mode": "mdi:tune-variant",
    "Control State": "mdi:state-machine",
    "Target Power": "mdi:target",
    "Target SOC": "mdi:battery-charging-100",
    "Meter Connection Status": "mdi:connection",
    "Meter Power": "mdi:home-lightning-bolt",
    "Bypass Power": "mdi:transmission-tower-export",
    "Emergency Power Supply": "mdi:alert-decagram",
    "DC Input Power 1": "mdi:solar-panel",
    "DC Input Power 2": "mdi:solar-panel",
    "DC Input Power 3": "mdi:solar-panel",
    "DC Input Power 4": "mdi:solar-panel",
}

# Enum-Mapping für hübsche Texte
ENUM_MAP = {
    "6001": {
        1000: "Idle",
        1001: "Charging",
        1002: "Discharging",
    },
    "7120": {
        1000: "ON",
        1001: "OFF",
    },
    "47005": {
        1: "Self-consumed prioritized",
        5: "Charge/Discharge Schedule",
    },
    "47015": {
        0: "Standby",
        1: "Charging",
        2: "Discharging",
    },
}


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Indevolt sensors from config entry."""
    coordinator: IndevoltDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    device_map = coordinator.device_map.get("entities", {})
    for key, meta in device_map.items():
        entities.append(
            IndevoltSensor(
                coordinator,
                entry.entry_id,
                key,
                meta.get("name"),
                meta.get("unit"),
                ICON_MAP.get(meta.get("name")),
            )
        )

    _LOGGER.debug(
        "Adding %d Indevolt sensors for model %s", len(entities), coordinator.model
    )
    async_add_entities(entities)


class IndevoltSensor(CoordinatorEntity, SensorEntity):
    """Representation of an Indevolt sensor."""

    def __init__(self, coordinator, entry_id, key, name, unit, icon):
        super().__init__(coordinator)
        self._key = str(key)
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_unique_id = f"indevolt_{entry_id}_{key}"
        self._attr_icon = icon
        self._entry_id = entry_id

    @property
    def native_value(self):
        """Return the sensor value."""
        raw = self.coordinator.data.get(self._key)

        # Wenn Enum → Mapping benutzen
        if raw is not None and self._key in ENUM_MAP:
            return ENUM_MAP[self._key].get(raw, f"Unknown ({raw})")

        return raw
