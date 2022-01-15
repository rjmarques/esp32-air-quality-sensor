"""Support for Esp32 Air Quality sensors."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    CONCENTRATION_PARTS_PER_MILLION,
    DEVICE_CLASS_CO2,
    DEVICE_CLASS_PM1,
    DEVICE_CLASS_PM10,
    DEVICE_CLASS_PM25,
    DEVICE_CLASS_VOLATILE_ORGANIC_COMPOUNDS,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    ATTR_CO2_CONCENTRATION,
    ATTR_VOC_INDEX,
    ATTR_PM1_CONCENTRATION,
    ATTR_PM2_CONCENTRATION,
    ATTR_PM10_CONCENTRATION,
)
from .coordinator import Esp32AQDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Esp32 Air Quality sensors based on a config entry."""
    coordinator: Esp32AQDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    sensors = [
        CO2Sensor(coordinator),
        PM1Sensor(coordinator),
        PM2Sensor(coordinator),
        PM10Sensor(coordinator),
        VOCSensor(coordinator),
    ]

    async_add_entities(sensors)


class Esp32AQEntity(CoordinatorEntity):
    """Defines a base Esp32 Air Quality entity."""

    coordinator: Esp32AQDataUpdateCoordinator

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this Esp32 AQ device."""
        return DeviceInfo(
            identifiers={
                (
                    DOMAIN,
                    self.coordinator.info.chip_id,
                )
            },
            name=f"{self.coordinator.info.chip_id}",
            model="ESP32",
            sw_version="1.0.0",
            configuration_url=f"http://{self.coordinator.host}",
        )


class CO2Sensor(Esp32AQEntity, SensorEntity):
    """Defines an Esp32 Air Quality CO2 sensor."""

    _attr_icon = "mdi:molecule-co2"
    _attr_native_unit_of_measurement = CONCENTRATION_PARTS_PER_MILLION
    _attr_device_class = DEVICE_CLASS_CO2

    def __init__(self, coordinator: Esp32AQDataUpdateCoordinator) -> None:
        """Initialize Esp32 Air Quality CO2 sensor."""
        super().__init__(coordinator=coordinator)
        self._unique_id = f"{self.coordinator.info.chip_id}_co2"
        self._attr_name = f"{self.coordinator.info.chip_id} CO2"

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the state attributes of the entity."""
        return {
            ATTR_CO2_CONCENTRATION: self.coordinator.data.co2,
        }

    @property
    def unique_id(self):
        """Return the unique id."""
        return self._unique_id

    @property
    def native_value(self) -> int:
        """Return the state of the sensor."""
        return self.coordinator.data.co2


class VOCSensor(Esp32AQEntity, SensorEntity):
    """Defines an Esp32 Air Quality VOC sensor."""

    _attr_icon = "mdi:scent"
    _attr_native_unit_of_measurement = "index"
    _attr_device_class = DEVICE_CLASS_VOLATILE_ORGANIC_COMPOUNDS

    def __init__(self, coordinator: Esp32AQDataUpdateCoordinator) -> None:
        """Initialize Esp32 Air Quality VOC sensor."""
        super().__init__(coordinator=coordinator)
        self._unique_id = f"{self.coordinator.info.chip_id}_voc"
        self._attr_name = f"{self.coordinator.info.chip_id} VOC"

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the state attributes of the entity."""
        return {
            ATTR_VOC_INDEX: self.coordinator.data.voc,
        }

    @property
    def unique_id(self):
        """Return the unique id."""
        return self._unique_id

    @property
    def native_value(self) -> int:
        """Return the state of the sensor."""
        return self.coordinator.data.voc


class PM1Sensor(Esp32AQEntity, SensorEntity):
    """Defines an Esp32 Air Quality PM1.0 sensor."""

    _attr_icon = "mdi:factory"
    _attr_native_unit_of_measurement = CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
    _attr_device_class = DEVICE_CLASS_PM1

    def __init__(self, coordinator: Esp32AQDataUpdateCoordinator) -> None:
        """Initialize Esp32 Air Quality PM1.0 sensor."""
        super().__init__(coordinator=coordinator)
        self._unique_id = f"{self.coordinator.info.chip_id}_pm1"
        self._attr_name = f"{self.coordinator.info.chip_id} PM1"

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the state attributes of the entity."""
        return {
            ATTR_PM1_CONCENTRATION: self.coordinator.data.pm1,
        }

    @property
    def unique_id(self):
        """Return the unique id."""
        return self._unique_id

    @property
    def native_value(self) -> int:
        """Return the state of the sensor."""
        return self.coordinator.data.pm1


class PM2Sensor(Esp32AQEntity, SensorEntity):
    """Defines an Esp32 Air Quality PM2.5 sensor."""

    _attr_icon = "mdi:factory"
    _attr_native_unit_of_measurement = CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
    _attr_device_class = DEVICE_CLASS_PM25

    def __init__(self, coordinator: Esp32AQDataUpdateCoordinator) -> None:
        """Initialize Esp32 Air Quality PM2.5 sensor."""
        super().__init__(coordinator=coordinator)
        self._unique_id = f"{self.coordinator.info.chip_id}_pm2"
        self._attr_name = f"{self.coordinator.info.chip_id} PM2.5"

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the state attributes of the entity."""
        return {
            ATTR_PM2_CONCENTRATION: self.coordinator.data.pm2,
        }

    @property
    def unique_id(self):
        """Return the unique id."""
        return self._unique_id

    @property
    def native_value(self) -> int:
        """Return the state of the sensor."""
        return self.coordinator.data.pm2


class PM10Sensor(Esp32AQEntity, SensorEntity):
    """Defines an Esp32 Air Quality PM10 sensor."""

    _attr_icon = "mdi:factory"
    _attr_native_unit_of_measurement = CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
    _attr_device_class = DEVICE_CLASS_PM10

    def __init__(self, coordinator: Esp32AQDataUpdateCoordinator) -> None:
        """Initialize Esp32 Air Quality PM10 sensor."""
        super().__init__(coordinator=coordinator)
        self._unique_id = f"{self.coordinator.info.chip_id}_pm10"
        self._attr_name = f"{self.coordinator.info.chip_id} PM10"

    @property
    def unique_id(self):
        """Return the unique id."""
        return self._unique_id

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the state attributes of the entity."""
        return {
            ATTR_PM10_CONCENTRATION: self.coordinator.data.pm10,
        }

    @property
    def native_value(self) -> int:
        """Return the state of the sensor."""
        return self.coordinator.data.pm10
