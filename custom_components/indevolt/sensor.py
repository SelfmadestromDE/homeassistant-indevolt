# custom_components/indevolt/sensor.py
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from . import DOMAIN

# Definiere hier die Sensoren die du im Dashboard sehen willst
# Key = cJson Punktnummer laut PDF
SENSOR_DEFINITIONS = {
    "1664": {"name": "Battery SOC", "unit": "%"},
    "1665": {"name": "Battery SOH", "unit": "%"},
    "1501": {"name": "Battery Voltage", "unit": "V"},
    "1502": {"name": "Battery Current", "unit": "A"},
    "2108": {"name": "Power Output", "unit": "W"},
    "6000": {"name": "Battery Power", "unit": "W"},
    "6001": {"name": "Battery Capacity", "unit": "Wh"},
    "6002": {"name": "Battery Rated Capacity", "unit": "Wh"}
}


class IndevoltSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, key: str, name: str, unit: str | None):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit

    @property
    def native_value(self):
        return self.coordinator.data.get(self._key)


async def async_setup_entry(hass, entry, async_add_entities):
    inst = hass.data[DOMAIN][entry.entry_id]
    coord = inst["coordinator"]

    entities = []
    for key, meta in SENSOR_DEFINITIONS.items():
        entities.append(IndevoltSensor(coord, key, meta["name"], meta["unit"]))
    async_add_entities(entities, True)

