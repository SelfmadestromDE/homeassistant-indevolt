import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfEnergy, UnitOfPower, UnitOfElectricPotential, UnitOfElectricCurrent, PERCENTAGE

from . import IndevoltDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# Mapping für Enums zu Text
ENUM_MAPPINGS = {
    "6001": {1000: "Idle", 1001: "Charging", 1002: "Discharging"},
    "7101": {1: "Self-consumed prioritized", 5: "Charge/Discharge Schedule"},
    "7120": {1000: "ON", 1001: "OFF"},
    "47005": {1: "Self-consumed prioritized", 2: "Charge/Discharge Schedule", 4: "Real-time Control"},
    "47015": {0: "Standby", 1: "Charging", 2: "Discharging"},
}

# Mapping für Enums zu Icons
ENUM_ICONS = {
    "6001": {1000: "mdi:battery", 1001: "mdi:battery-charging", 1002: "mdi:battery-arrow-down"},
    "7101": {1: "mdi:solar-power", 5: "mdi:clock-outline"},
    "7120": {1000: "mdi:lan-connect", 1001: "mdi:lan-disconnect"},
    "47005": {1: "mdi:solar-power", 2: "mdi:clock-outline", 4: "mdi:access-point"},
    "47015": {0: "mdi:power-standby", 1: "mdi:battery-charging", 2: "mdi:battery-arrow-down"},
}

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Indevolt sensors."""
    coordinator: IndevoltDataUpdateCoordinator = hass.data["indevolt"][entry.entry_id]

    sensors = []
    for key, meta in coordinator.device_map.items():
        sensors.append(
            IndevoltSensor(
                coordinator,
                entry,
                key,
                meta.get("name", f"Sensor {key}"),
                meta.get("unit")
            )
        )
    async_add_entities(sensors)


class IndevoltSensor(SensorEntity):
    """Representation of an Indevolt sensor."""

    def __init__(self, coordinator, entry, key, name, unit):
        self.coordinator = coordinator
        self._key = key
        self._attr_name = f"{name}"
        self._attr_native_unit_of_measurement = unit
        self._attr_unique_id = f"indevolt_{entry.entry_id}_{key}"

    @property
    def native_value(self):
        val = self.coordinator.data.get(self._key)
        if val is None:
            return None

        # Enum-Mapping
        if self._key in ENUM_MAPPINGS:
            return ENUM_MAPPINGS[self._key].get(val, f"Unknown ({val})")

        return val

    @property
    def icon(self):
        """Return an icon based on SOC or enum state."""
        val = self.coordinator.data.get(self._key)
        if val is None:
            return None

        # ⚡️ Battery SOC logic (6002)
        if self._key == "6002":
            soc = int(val)

            # Basis-SOC-Icon bestimmen
            if soc >= 95:
                base_icon = "mdi:battery"
            elif soc >= 90:
                base_icon = "mdi:battery-90"
            elif soc >= 80:
                base_icon = "mdi:battery-80"
            elif soc >= 70:
                base_icon = "mdi:battery-70"
            elif soc >= 60:
                base_icon = "mdi:battery-60"
            elif soc >= 50:
                base_icon = "mdi:battery-50"
            elif soc >= 40:
                base_icon = "mdi:battery-40"
            elif soc >= 30:
                base_icon = "mdi:battery-30"
            elif soc >= 20:
                base_icon = "mdi:battery-20"
            elif soc >= 10:
                base_icon = "mdi:battery-10"
            else:
                base_icon = "mdi:battery-alert-variant"

            # Prüfen ob Lade-/Entlade-Status verfügbar ist
            charge_state = self.coordinator.data.get("6001")
            alt_state = self.coordinator.data.get("47015")

            if charge_state in (1001,) or alt_state in (1,):  # Charging
                return base_icon.replace("mdi:battery", "mdi:battery-charging")
            elif charge_state in (1002,) or alt_state in (2,):  # Discharging
                return "mdi:battery-arrow-down"

            return base_icon

        # Enum-Icons
        if self._key in ENUM_ICONS:
            return ENUM_ICONS[self._key].get(val)

        return None

    @property
    def should_poll(self):
        return False

    async def async_update(self):
        await self.coordinator.async_request_refresh()
