"""Module for querying Esp32 Air Quality Device."""

import sys


import aiohttp
import asyncio

from .core import Esp32AirQuality
from .exceptions import Esp32AQError


async def main(loop):
    """Main method for the script."""
    if len(sys.argv) < 2:
        print("please provide device hostname/ip")
        sys.exit(2)
    host = sys.argv[1]

    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout, loop=loop) as session:
        eaq = Esp32AirQuality(host, session)
        try:
            await eaq.connect()
            readings = await eaq.get_readings()

            print("readings...")
            print("co2: " + str(readings.co2))
            print("pm1.0: " + str(readings.pm1))
            print("pm2.5: " + str(readings.pm2))
            print("pm10.0: " + str(readings.pm10))
            print("voc: " + str(readings.voc))
        except Esp32AQError as error:
            print("failed to get readings: " + str(error))


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
