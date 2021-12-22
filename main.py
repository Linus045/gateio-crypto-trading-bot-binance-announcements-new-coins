import gateio_new_coins_announcements_bot.trade_client as trade_client
from gateio_new_coins_announcements_bot.load_config import load_config
from gateio_new_coins_announcements_bot.logger import init_logger
from gateio_new_coins_announcements_bot.main import main
from gateio_new_coins_announcements_bot.new_listings_scraper import init_listings_scraper
from gateio_new_coins_announcements_bot.send_telegram import init_telegram
from gateio_new_coins_announcements_bot.trade_client import init_trade_client

if __name__ == "__main__":
    load_config("config.yml")
    init_logger()

    init_trade_client("auth/auth.yml")
    init_telegram("auth/auth.yml")
    init_listings_scraper(trade_client.get_spot_api())

    # TODO: refactor this main call
    main()
