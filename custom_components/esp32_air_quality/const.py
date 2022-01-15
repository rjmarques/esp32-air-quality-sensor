"""Constants for the ESP32 Air Quality integration."""
from datetime import timedelta
import logging

# Integration domain
DOMAIN = "esp32_air_quality"

LOGGER = logging.getLogger(__package__)
SCAN_INTERVAL = timedelta(seconds=60)

# Attributes
ATTR_CO2_CONCENTRATION = "concentration"
ATTR_VOC_INDEX = "index"
ATTR_PM1_CONCENTRATION = "concentration"
ATTR_PM2_CONCENTRATION = "concentration"
ATTR_PM10_CONCENTRATION = "concentration"
