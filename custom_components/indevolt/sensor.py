import logging
from homeassistant.helpers.entity import Entity
from homeassistant.components.number import NumberEntity
from homeassistant.components.button import ButtonEntity

_LOGGER = logging.getLogger(__name__)

# Define Icons for different sensors
ICON_MAP = {
    "Grid Charge Mode": "mdi:flash",
    "Grid Charge Power": "mdi:flash-circle",
    "Target SOC": "mdi:battery-charging-100",
    "Battery SOC": "mdi:battery",
    "Battery State": "mdi:battery-heart-variant",
    "Battery Power": "mdi:flash",
    "Battery Daily Charging Energy": "mdi:battery-plus",
    "Battery Daily Discharging Energy": "mdi:battery-minus",
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

class GridChargePower(NumberEntity):
    """Grid Charge Power or Discharge Power (W)"""
    
    def __init__(self, coordinator, entry_id, mode):
        self.coordinator = coordinator
        self._entry_id = entry_id
        self._mode = mode
        self._attr_name = f"Grid {mode.capitalize()} Power"
        self._attr_unit_of_measurement = "W"
        
        # Max Power depending on mode
        self._attr_max_value = 1200 if mode == "charge" else 800
        self._attr_min_value = 0
        self._attr_step = 10

    @property
    def native_value(self):
        """Return the power."""
        return self.coordinator.data.get(f"grid_charge_{self._mode}", 0)

    async def async_set_native_value(self, value: int):
        """Set the power."""
        value = min(max(value, 0), self._attr_max_value)
        await self.coordinator.client.set_data({"f": 16, "t": 47016, "v": [value]})

class GridChargeSOC(NumberEntity):
    """Target SOC (percentage)"""
    
    def __init__(self, coordinator, entry_id):
        self.coordinator = coordinator
        self._entry_id = entry_id
        self._attr_name = "Target SOC"
        self._attr_unit_of_measurement = "%"
        self._attr_min_value = 0
        self._attr_max_value = 100
        self._attr_step = 1

    @property
    def native_value(self):
        """Return the SOC value."""
        return self.coordinator.data.get("soc", 100)

    async def async_set_native_value(self, value: int):
        """Set the SOC value."""
        await self.coordinator.client.set_data({"f": 16, "t": 47017, "v": [value]})

class ApplyGridChargeButton(ButtonEntity):
    """Button to apply the grid charge settings."""
    
    def __init__(self, coordinator, entry_id):
        self.coordinator = coordinator
        self._entry_id = entry_id
        self._attr_name = "Apply Grid Charge"

    async def async_press(self):
        """Trigger the grid charge apply action."""
        mode = self.coordinator.data.get("mode", 1)
        power = self.coordinator.data.get("power", 0)
        soc = self.coordinator.data.get("soc", 100)
        
        # Send data to device
        await self.coordinator.client.set_data({"f": 16, "t": 47015, "v": [mode, power, soc]})

class IndevoltSensor(SensorEntity):
    """Representation of an Indevolt sensor."""

    def __init__(self, coordinator, entry_id, key, name, unit, icon):
        self.coordinator = coordinator
        self._key = key
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_unique_id = f"indevolt_{entry_id}_{key}"
        self._attr_icon = icon
        self._entry_id = entry_id

    @property
    def native_value(self):
        """Return the sensor value."""
        raw = self.coordinator.data.get(self._key)

        # If Enum → use the mapping
        if raw is not None and self._key in ENUM_MAP:
            return ENUM_MAP[self._key].get(raw, f"Unknown ({raw})")

        return raw
