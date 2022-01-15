"""Models for Esp32 Air Quality"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Readings:
    """Data that can be obtained from an Esp32 Air Quality device."""

    co2: int
    voc: int
    pm1: float
    pm2: float
    pm10: float

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Readings:
        """Return Readings object from Device API response.
        Args:
            data: The data from the Esp32 AQ device API.
        Returns:
            A Readings object.
        """
        return Readings(
            voc=int(data["voc"]),
            co2=int(data["co2"]),
            pm1=float(data["pm1.0"]),
            pm2=float(data["pm2.5"]),
            pm10=float(data["pm10.0"]),
        )


@dataclass
class DeviceInfo:
    """ESP32 device info."""

    chip_id: str
    core_count: str
    silicon_revision: str
    flash: str
    mac_address: str

    @staticmethod
    def from_dict(data: dict[str, Any]) -> DeviceInfo:
        """Return DeviceInfo object from Device API response.
        Args:
            data: The data from the Esp32 AQ device API.
        Returns:
            A DeviceInfo object.
        """
        return DeviceInfo(
            chip_id=data["chipID"],
            core_count=data["coreCount"],
            silicon_revision=data["siliconRevision"],
            flash=data["flash"],
            mac_address=data["macAddress"],
        )
