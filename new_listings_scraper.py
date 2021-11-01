import ast
import os.path
import re
import time

import requests
from gate_api import ApiClient, SpotApi

from auth.gateio_auth import *
from logger import logger
from store_order import *
from trade_client import *

client = load_gateio_creds('auth/auth.yml')
spot_api = SpotApi(ApiClient(client))

global supported_currencies

def get_coins(pairing, new_listings):
    """
    Scrapes new listings page for and returns new Symbols when appropriate
    """
    
    if len(new_listings) == 0:
        return None
    else:
        symbol = new_listings[0]

    latest_announcement = f"Will list ({symbol})"

    if "adds" in latest_announcement.lower() and "trading pairs" in latest_announcement.lower() and pairing in latest_announcement:
        found_pairs = re.findall(r'[A-Z]{1,10}[/][A-Z]*', latest_announcement)
        found_coins = [i.replace(f'/{pairing}', "") for i in found_pairs if i.find(pairing) != -1]
        return found_coins
    elif "will list" in latest_announcement.lower():
        found_coins = re.findall('\(([^)]+)', latest_announcement)
        if(len(found_coins) > 0):
            return found_coins
    
    return None


def get_last_coin(pairing, new_listings):
    logger.debug("Pulling announcement page for [adds + trading pairs] or [will list] scenarios")

    found_coins = get_coins(pairing, new_listings)
    
    if len(found_coins) > 0:
        return found_coins
    
    return None


def get_new_listings(file):
    """
    Get user inputed new listings (see https://www.gate.io/en/marketlist?tab=newlisted)
    """
    with open(file, "r+") as f:
        return json.load(f)

def store_newly_listed(listings):
    """
    Save order into local json file
    """
    with open('newly_listed.json', 'w') as f:
        json.dump(listings, f, indent=4)


def store_new_listing(listing):
    """
    Only store a new listing if different from existing value
    """

    if os.path.isfile('new_listing.json'):
        file = load_order('new_listing.json')
        if set(listing) == set(file):
            return file
        else:
            joined = file + listing
            
            with open('new_listing.json', 'w') as f:
                json.dump(joined, f, indent=4)
            
            logger.info("New listing detected, updating file")
            return file
    else:
        new_listing = store_order('new_listing.json', listing)
        logger.info("File does not exist, creating file")

        return new_listing


def search_and_update(pairing, new_listings):
    """
    Pretty much our main func
    """

    count = 57
    while True:
        time.sleep(3)
        try:
            latest_coins = get_last_coin(pairing, new_listings)
            if len(latest_coins) > 0:
                last_price = get_last_price(latest_coins[0], pairing)
                if len(last_price) > 0 and float(last_price) > 0:

                    logger.info(f"Found new coin {latest_coins[0]} with price of {last_price}!! Adding to new listings.")
                   
                    # store as announcement coin for main thread to pick up (It's go time!!!)
                    store_new_listing(latest_coins)

                    # remove from list of coins to be listed
                    new_listings.pop(0)
                    logger.info(f'Removing the search for {latest_coins[0]} from the searching thread')
            
            count = count + 3
            if count % 60 == 0:
                logger.info("One minute has passed.  Checking for coin announcements every 3 seconds (in a separate thread)")
                count = 0
        except GateApiException as e:
            if e.label != "INVALID_CURRENCY":
                logger.error(e)
            else:
                logger.info("Gate.io return INVALID_CURRENCY when trying to get latest price. Keep trying.")
        except Exception as e:
            logger.info(e)


def get_all_currencies(single=False):
    """
    Get a list of all currencies supported on gate io
    :return:
    """
    global supported_currencies
    while True:
        logger.info("Getting the list of supported currencies from gate io")
        response = spot_api.list_currencies()
        all_currencies = ast.literal_eval(str(response))
        currency_list = [currency['currency'] for currency in all_currencies]
        with open('currencies.json', 'w') as f:
            json.dump(currency_list, f, indent=4)
            logger.info("List of gate io currencies saved to currencies.json. Waiting 1 "
                  "second before refreshing list...")
        supported_currencies = currency_list
        if single:
            return supported_currencies
        else:
            time.sleep(300)
