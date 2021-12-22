import ast
import json
import os.path
import random
import re
import string
import time

import requests

import gateio_new_coins_announcements_bot.globals as globals
from gateio_new_coins_announcements_bot.load_config import get_config
from gateio_new_coins_announcements_bot.logger import LOG_DEBUG
from gateio_new_coins_announcements_bot.logger import LOG_INFO
from gateio_new_coins_announcements_bot.store_order import load_order

_supported_currencies = None
_previously_found_coins = set()


def init_listings_scraper(spot_api):
    global _spot_api
    _spot_api = spot_api


def generate_binance_announcement_query():
    # Generate random query/params to help prevent caching
    rand_page_size = random.randint(1, 200)
    letters = string.ascii_letters
    random_string = "".join(random.choice(letters) for i in range(random.randint(10, 20)))
    random_number = random.randint(1, 99999999999999999999)
    queries = [
        "type=1",
        "catalogId=48",
        "pageNo=1",
        f"pageSize={str(rand_page_size)}",
        f"rnd={str(time.time())}",
        f"{random_string}={str(random_number)}",
    ]
    random.shuffle(queries)
    LOG_DEBUG(f"Queries: {queries}")
    return (
        f"https://www.binancezh.com/gateway-api/v1/public/cms/article/list/query"
        f"?{queries[0]}&{queries[1]}&{queries[2]}&{queries[3]}&{queries[4]}&{queries[5]}"
    )


def generate_kucoin_announcement_query():
    # Generate random query/params to help prevent caching
    rand_page_size = random.randint(1, 200)
    letters = string.ascii_letters
    random_string = "".join(random.choice(letters) for i in range(random.randint(10, 20)))
    random_number = random.randint(1, 99999999999999999999)
    queries = [
        "page=1",
        f"pageSize={str(rand_page_size)}",
        "category=listing",
        "lang=en_US",
        f"rnd={str(time.time())}",
        f"{random_string}={str(random_number)}",
    ]
    random.shuffle(queries)
    LOG_DEBUG(f"Queries: {queries}")
    return (
        f"https://www.kucoin.com/_api/cms/articles?"
        f"?{queries[0]}&{queries[1]}&{queries[2]}&{queries[3]}&{queries[4]}&{queries[5]}"
    )


def get_kucoin_announcement():
    request_url = generate_kucoin_announcement_query()
    latest_announcement = requests.get(request_url)
    try:
        LOG_DEBUG(f'X-Cache: {latest_announcement.headers["X-Cache"]}')
    except KeyError:
        # No X-Cache header was found - great news, we're hitting the source.
        pass
    latest_announcement = latest_announcement.json()
    LOG_DEBUG("Finished pulling announcement page")
    return latest_announcement["items"][0]["title"]


def get_binance_announcement():
    request_url = generate_binance_announcement_query()
    latest_announcement = requests.get(request_url)
    LOG_DEBUG("Finished pulling announcement page")
    try:
        LOG_DEBUG(f'X-Cache: {latest_announcement.headers["X-Cache"]}')
    except KeyError:
        # No X-Cache header was found - great news, we're hitting the source.
        pass
    latest_announcement = latest_announcement.json()
    return latest_announcement["data"]["catalogs"][0]["articles"][0]["title"]


def get_last_coin():
    """
    Returns new Symbol when appropriate
    """
    found_coin = None
    uppers = None

    config = get_config()
    check_kucoin_announcements = config["TRADE_OPTIONS"]["KUCOIN_ANNOUNCEMENTS"] is True

    # scan Binance Announcement
    latest_announcement = get_binance_announcement()
    if "Will List" in latest_announcement:
        found_coins = re.findall(r"\(([^)]+)", latest_announcement)
        if len(found_coins) > 0:
            found_coin = found_coins[0]
            if found_coin != globals.latest_listing and found_coin not in _previously_found_coins:
                uppers = found_coin
                _previously_found_coins.add(uppers)
                LOG_INFO("New coin detected: " + uppers)

    # if no result on binance and  check Kucoin Announcements if its enabled
    if uppers is None and check_kucoin_announcements:
        LOG_INFO("Kucoin announcements enabled, look for new Kucoin coins...")
        kucoin_coin = None
        kucoin_announcement = get_kucoin_announcement()
        if "Gets Listed" in kucoin_announcement:
            kucoin_coins = re.findall(r"\(([^)]+)", kucoin_announcement)
            if len(kucoin_coins) > 0:
                kucoin_coin = kucoin_coins[0]

                # if the latest Binance announcement is not a new coin listing,
                # or the listing has already been returned, check kucoin
                if kucoin_coin != globals.latest_listing and kucoin_coin not in _previously_found_coins:
                    uppers = kucoin_coin
                    _previously_found_coins.add(uppers)
                    LOG_INFO("New Kucoin coin detected: " + uppers)
    print(f"{uppers=}")
    return uppers


def store_new_listing(listing):
    """
    Only store a new listing if different from existing value
    """
    if listing and not listing == globals.latest_listing:
        LOG_INFO("New listing detected")
        globals.latest_listing = listing
        globals.buy_ready.set()


def search_and_update():
    """
    Pretty much our main func
    """
    while not globals.stop_threads:
        sleep_time = 3
        for x in range(sleep_time):
            time.sleep(1)
            if globals.stop_threads:
                break
        try:
            latest_coin = get_last_coin()
            if latest_coin:
                store_new_listing(latest_coin)
            elif globals.test_mode and os.path.isfile("test_new_listing.json"):
                store_new_listing(load_order("test_new_listing.json"))
                if os.path.isfile("test_new_listing.json.used"):
                    os.remove("test_new_listing.json.used")
                os.rename("test_new_listing.json", "test_new_listing.json.used")
            LOG_INFO(f"Checking for coin announcements every {str(sleep_time)} seconds (in a separate thread)")
        except Exception as e:
            LOG_INFO(e)
    else:
        LOG_INFO("while loop in search_and_update() has stopped.")


def get_all_currencies(single=False):
    """
    Get a list of all currencies supported on gate io
    :return:
    """
    global _supported_currencies
    while not globals.stop_threads:
        LOG_INFO("Getting the list of supported currencies from gate io")
        all_currencies = ast.literal_eval(str(_spot_api.list_currencies()))
        currency_list = [currency["currency"] for currency in all_currencies]
        with open("currencies.json", "w") as f:
            json.dump(currency_list, f, indent=4)
            LOG_INFO(
                "List of gate io currencies saved to currencies.json. Waiting 5 " "minutes before refreshing list..."
            )
        _supported_currencies = currency_list
        if single:
            return _supported_currencies
        else:
            for x in range(300):
                time.sleep(1)
                if globals.stop_threads:
                    break
    else:
        LOG_INFO("while loop in get_all_currencies() has stopped.")


def load_old_coins():
    if os.path.isfile("old_coins.json"):
        with open("old_coins.json") as json_file:
            data = json.load(json_file)
            LOG_DEBUG("Loaded old_coins from file")
            return data
    else:
        return []


def store_old_coins(old_coin_list):
    with open("old_coins.json", "w") as f:
        json.dump(old_coin_list, f, indent=2)
        LOG_DEBUG("Wrote old_coins to file")
