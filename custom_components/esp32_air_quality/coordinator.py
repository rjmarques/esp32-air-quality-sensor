# """DataUpdateCoordinator for Esp32 Air Quality."""
from __future__ import annotations

from .esp32aq import Esp32AirQuality, Readings, Esp32AQError, DeviceInfo

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    LOGGER,
    SCAN_INTERVAL,
)


class Esp32AQDataUpdateCoordinator(DataUpdateCoordinator[Readings]):
    """Class to manage fetching Esp32 Air Quality data from single endpoint."""

    def __init__(
        self,
        hass: HomeAssistant,
        *,
        entry: ConfigEntry,
    ) -> None:
        """Initialize global WLED data updater."""
        host = entry.data[CONF_HOST]
        self.esp32aq = Esp32AirQuality(host, session=async_get_clientsession(hass))
        self.info: DeviceInfo = None
        self.host = host

        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
            update_method=self._async_update_data,
        )

    async def _async_update_data(self) -> Readings:
        """Fetch data from API endpoint"""

        try:
            # connect to the device the first time
            if not self.esp32aq.connected:
                await self.esp32aq.connect()
                self.info = self.esp32aq.get_device_info()

            readings = await self.esp32aq.get_readings()
            return readings
        except Esp32AQError as error:
            raise UpdateFailed(f"Error communicating with API: {error}")
