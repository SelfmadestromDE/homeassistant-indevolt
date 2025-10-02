import logging
from homeassistant.helpers.entity import Entity
from homeassistant.components.select import SelectEntity
from homeassistant.components.number import NumberEntity
from homeassistant.helpers import entity_platform
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Grid Charge control."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    device_map = coordinator.device_map.get("entities", {})

    if "grid_charge" in device_map:
        meta = device_map["grid_charge"]
        async_add_entities([GridChargeEntity(coordinator, entry.entry_id, meta)])

class GridChargeEntity(Entity):
    """Grid Charge control for Indevolt."""

    def __init__(self, coordinator, entry_id, meta):
        self.coordinator = coordinator
        self._entry_id = entry_id
        self._meta = meta
        self._attr_name = meta.get("name", "Grid Charge")
        self._mode = 1  # Default mode is Charging
        self._power = 0  # Default power
        self._soc = 100  # Default SOC to 100%

    @property
    def extra_state_attributes(self):
        """State attributes for this entity."""
        return {
            "mode": self._mode,
            "power": self._power,
            "soc": self._soc,
        }

    @property
    def icon(self):
        """Icon for the entity."""
        return "mdi:flash"

    @property
    def state(self):
        """State as a string."""
        return f"Mode: {self._mode}, Power: {self._power}W, SOC: {self._soc}%"

    @property
    def mode(self):
        """Return the current mode (Charging or Discharging)."""
        return self._mode

    @property
    def power(self):
        """Return the power in watts."""
        return self._power

    @property
    def soc(self):
        """Return the target SOC."""
        return self._soc

    async def async_set_mode(self, mode: int):
        """Set the mode (Charging or Discharging)."""
        if mode in [1, 2]:
            self._mode = mode
        else:
            raise ValueError("Invalid mode value")

    async def async_set_power(self, power: int):
        """Set the power depending on the mode."""
        if self._mode == 1:  # Charging mode
            self._power = min(max(power, 0), 1200)
        else:  # Discharging mode
            self._power = min(max(power, 0), 800)

    async def async_set_soc(self, soc: int):
        """Set the target SOC value."""
        self._soc = min(max(soc, 0), 100)

    async def apply_changes(self):
        """Send the command to the Indevolt device."""
        payload = {"f": 16, "t": 47015, "v": [self._mode, self._power, self._soc]}
        _LOGGER.debug("Sending Grid Charge payload: %s", payload)
        await self.coordinator.client.set_data(payload)
