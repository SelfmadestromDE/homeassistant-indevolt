import logging
from homeassistant.components.number import NumberEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN, IndevoltDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator: IndevoltDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    for key, meta in coordinator.device_map.get("entities", {}).items():
        if meta.get("platform") != "number":
            continue
        entities.append(
            IndevoltNumber(
                coordinator,
                entry.entry_id,
                key,
                meta.get("name"),
                meta.get("unit"),
                meta.get("min", 0),
                meta.get("max", 100),
                meta.get("step", 1),
            )
        )

    _LOGGER.debug("Adding %d Indevolt numbers", len(entities))
    async_add_entities(entities)


class IndevoltNumber(CoordinatorEntity, NumberEntity):
    def __init__(self, coordinator, entry_id, key, name, unit, min_v, max_v, step):
        super().__init__(coordinator)
        self._key = str(key)
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_unique_id = f"indevolt_{entry_id}_{key}"
        self._static_min = min_v
        self._static_max = max_v
        self._step = step

    @property
    def native_min_value(self):
        return self._static_min

    @property
    def native_max_value(self):
        # Dynamische Logik für Target Power (47016)
        if self._key == "47016":
            control_state = self.coordinator.data.get("47015")
            if control_state == 1:  # Charging
                return 1200
            elif control_state == 2:  # Discharging
                return 800
            else:
                return 0
        return self._static_max

    @property
    def native_step(self):
        return self._step

    @property
    def native_value(self):
        return self.coordinator.data.get(self._key)

    async def async_set_native_value(self, value: float):
        await self.coordinator.client.async_setdata(int(self._key), [value])
        await self.coordinator.async_request_refresh()
