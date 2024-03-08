#!/usr/bin/python3

import asyncio
import logging
import traceback

from aiohttp import ClientSession

from .solcastapi import ConnectionOptions, SolcastApi

# logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger(__name__)


async def test():
    try:
        options = ConnectionOptions(
            "changetoyourapikey", "https://api.solcast.com.au", "solcast.json"
        )

        async with ClientSession() as session:
            solcast = SolcastApi(session, options, apiCacheEnabled=True)
            await solcast.sites_data()
            await solcast.load_saved_data()
            print("Total today " + str(solcast.get_total_kwh_forecast_today()))
            print("Peak today " + str(solcast.get_peak_w_today()))
            print("Peak time today " + str(solcast.get_peak_w_time_today()))
    except Exception:
        _LOGGER.error("async_setup_entry: %s", traceback.format_exc())
        return False


asyncio.run(test())
