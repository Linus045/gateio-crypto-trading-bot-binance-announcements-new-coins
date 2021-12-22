import logging

import requests
import yaml

from gateio_new_coins_announcements_bot.load_config import get_config

_valid_auth = False
_bot_token = None
_bot_chatID = None


def init_telegram(auth_path):
    global _valid_auth, _bot_token, _bot_chatID
    with open(auth_path) as file:
        try:
            creds = yaml.load(file, Loader=yaml.FullLoader)
            _bot_token = str(creds["telegram_token"])
            _bot_chatID = str(creds["telegram_chat_id"])
            _valid_auth = True
        except KeyError:
            _valid_auth = False
            pass


class TelegramLogFilter(logging.Filter):
    # filter for logRecords with TELEGRAM extra
    def filter(self, record):
        return hasattr(record, "TELEGRAM")


class TelegramHandler(logging.Handler):
    # log to telegram if the TELEGRAM extra matches an enabled key
    def emit(self, record):

        if not _valid_auth:
            return

        key = getattr(record, "TELEGRAM")

        config = get_config()
        # unknown message key
        if key not in config["TELEGRAM"]["NOTIFICATIONS"]:
            return

        # message key disabled
        if not config["TELEGRAM"]["NOTIFICATIONS"][key]:
            return

        requests.get(
            f"""https://api.telegram.org/bot{_bot_token}/sendMessage
            ?chat_id={_bot_chatID}
            &parse_mode=Markdown
            &text={record.message}"""
        )
