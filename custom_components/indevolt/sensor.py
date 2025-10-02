import logging
from homeassistant.helpers.entity import Entity
from homeassistant.components.select import SelectEntity
from homeassistant.components.number import NumberEntity
from homeassistant.components.button import ButtonEntity
from homeassistant.components.sensor import SensorEntity

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
}

class GridChargeMode(SelectEntity):
    """Grid Charge Mode (Charging/Discharging)"""
    
    def __init__(self, coordinator, entry_id):
        self.coordinator = coordinator
        self._entry_id = entry_id
        self._attr_name = "Grid Charge Mode"
        self._attr_options = ["Charging", "Discharging"]

    @property
    def current_option(self):
        """Return the current option (charging or discharging)."""
        return "Charging" if self.coordinator.data.get("mode", 1) == 1 else "Discharging"

    async def async_select_option(self, option: str):
        """Set the mode."""
        mode = 1 if option == "Charging" else 2
        await self.coordinator.client.set_data({"f": 16, "t": 47015, "v": [mode]})

class GridChargePower(NumberEntity):
    """Grid Charge Power (W)"""
    
    def __init__(self, coordinator, entry_id):
        self.coordinator = coordinator
        self._entry_id = entry_id
        self._attr_name = "Grid Charge Power"
        self._attr_unit_of_measurement = "W"
        self._attr_min_value = 0
        self._attr_max_value = 1200
        self._attr_step = 10

    @property
    def native_value(self):
        """Return the power."""
        return self.coordinator.data.get("power", 0)

    async def async_set_native_value(self, value: int):
        """Set the power."""
        value = min(max(value, 0), 1200)
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
