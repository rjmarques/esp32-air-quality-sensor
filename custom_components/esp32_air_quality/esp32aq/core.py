"""
Esp32 Air Quality interface implementation
"""

import logging
from typing import Any

import aiohttp
from aiohttp.client_exceptions import ClientError

from .models import DeviceInfo, Readings
from .exceptions import Esp32AQError

_LOGGER = logging.getLogger(__name__)


class Esp32AirQuality:
    """Interacts with my Esp32 Air Quality device via public API."""

    def __init__(self, host: str, session: aiohttp.client.ClientSession) -> None:
        self.host = host
        self.session = session
        self.dev_info = None
        self.connected = False

    async def connect(self):
        """Connect to device and fetch device data."""
        if self.connected:
            return

        try:
            self.dev_info = await self._fetch_device_info()
            self.connected = True
        except ClientError as error:
            raise Esp32AQError(error)

    async def get_readings(self) -> Readings:
        """Fetch and return all the sensor data."""
        url = self._build_url("/readings")
        data = await self._fetch_json(url)
        return Readings.from_dict(data)

    def get_device_info(self) -> DeviceInfo:
        """Return the device's basic information"""
        if not self.connected:
            raise Esp32AQError("not yet connected to device")

        return self.dev_info

    async def _fetch_device_info(self) -> DeviceInfo:
        """Fetch the device's hardware information"""
        url = self._build_url("/")
        data = await self._fetch_json(url)
        return DeviceInfo.from_dict(data)

    async def _fetch_json(self, url: str) -> Any:
        try:
            response = await self.session.get(url)
            response.raise_for_status()
            data = await response.json()
            return data
        except ClientError as error:
            raise Esp32AQError(error)

    def _build_url(self, endpoint: str) -> str:
        return "http://" + self.host + endpoint
