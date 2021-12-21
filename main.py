from gateio_new_coins_announcements_bot.load_config import load_config
from gateio_new_coins_announcements_bot.logger import init_logger
from gateio_new_coins_announcements_bot.main import main
from gateio_new_coins_announcements_bot.new_listings_scraper import init_listings_scraper

if __name__ == "__main__":
    load_config("config.yml")
    init_logger()
    init_listings_scraper("auth/auth.yml")

    # TODO: refactor this main call
    main()
