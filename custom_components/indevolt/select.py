import logging
from homeassistant.components.select import SelectEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN, IndevoltDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Indevolt selects from config entry."""
    coordinator: IndevoltDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    device_map = coordinator.device_map.get("entities", {})

    for key, meta in device_map.items():
        if "enum" in meta:  # Nur Enums
            entities.append(
                IndevoltSelect(
                    coordinator,
                    entry.entry_id,
                    key,
                    meta.get("name"),
                    meta.get("enum"),
                )
            )

    _LOGGER.debug(
        "Adding %d Indevolt selects for model %s", len(entities), coordinator.model
    )
    async_add_entities(entities)


class IndevoltSelect(CoordinatorEntity, SelectEntity):
    """Representation of an Indevolt select."""

    def __init__(self, coordinator, entry_id, key, name, options):
        super().__init__(coordinator)
        self._key = str(key)
        self._attr_name = name
        self._attr_unique_id = f"indevolt_{entry_id}_{key}"
        self._options_map = {int(k): v for k, v in options.items()}  # {1000:"Static"}
        self._reverse_map = {v: k for k, v in self._options_map.items()}  # {"Static":1000}
        self._attr_options = list(self._options_map.values())

    @property
    def current_option(self):
        raw = self.coordinator.data.get(self._key)
        return self._options_map.get(raw)

    async def async_select_option(self, option: str):
        """Set a new option on the device."""
        if option not in self._reverse_map:
            _LOGGER.error("Invalid option %s for %s", option, self._attr_name)
            return
        value = self._reverse_map[option]
        _LOGGER.debug("Setting %s (%s) to %s", self._attr_name, self._key, option)
        await self.coordinator.client.async_setdata(self._key, value)
        await self.coordinator.async_request_refresh()
