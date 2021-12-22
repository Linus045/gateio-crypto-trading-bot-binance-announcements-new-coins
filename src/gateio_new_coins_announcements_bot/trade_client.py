from datetime import datetime

from gate_api import ApiClient
from gate_api import Order
from gate_api import SpotApi

from gateio_new_coins_announcements_bot.auth.gateio_auth import load_gateio_creds
from gateio_new_coins_announcements_bot.logger import LOG_DEBUG
from gateio_new_coins_announcements_bot.logger import LOG_ERROR
from gateio_new_coins_announcements_bot.logger import LOG_INFO

_last_trade = None
_spot_api = None


def init_trade_client(auth_path):
    global _spot_api
    client = load_gateio_creds(auth_path)
    _spot_api = SpotApi(ApiClient(client))


def get_spot_api():
    return _spot_api


def get_last_price(base, quote, return_price_only):
    """
    Args:
    'DOT', 'USDT'
    """
    global _last_trade
    trades = _spot_api.list_trades(currency_pair=f"{base}_{quote}", limit=1)
    assert len(trades) == 1
    trade = trades[0]

    create_time_ms = datetime.utcfromtimestamp(int(trade.create_time_ms.split(".")[0]) / 1000)
    create_time_formatted = create_time_ms.strftime("%d-%m-%y %H:%M:%S.%f")

    if _last_trade and _last_trade.id > trade.id:
        LOG_DEBUG("STALE TRADEBOOK RESULT FOUND. RE-TRYING.")
        return get_last_price(base=base, quote=quote, return_price_only=return_price_only)
    else:
        _last_trade = trade

    if return_price_only:
        return trade.price

    LOG_INFO(
        f"LATEST TRADE: {trade.currency_pair} | id={trade.id} | create_time={create_time_formatted} | "
        f"side={trade.side} | amount={trade.amount} | price={trade.price}"
    )
    return trade


def get_min_amount(base, quote):
    """
    Args:
    'DOT', 'USDT'
    """
    try:
        min_amount = _spot_api.get_currency_pair(currency_pair=f"{base}_{quote}").min_quote_amount
    except Exception as e:
        LOG_ERROR(e)
    else:
        return min_amount


def place_order(base, quote, amount, side, last_price):
    """
    Args:
    'DOT', 'USDT', 50, 'buy', 400
    """
    try:
        order = Order(
            amount=str(float(amount) / float(last_price)),
            price=last_price,
            side=side,
            currency_pair=f"{base}_{quote}",
            time_in_force="ioc",
        )
        order = _spot_api.create_order(order)
        t = order
        LOG_INFO(
            f"PLACE ORDER: {t.side} | {t.id} | {t.account} | {t.type} | {t.currency_pair} | {t.status} | "
            f"amount={t.amount} | price={t.price} | left={t.left} | filled_total={t.filled_total} | "
            f"fill_price={t.fill_price} | fee={t.fee} {t.fee_currency}"
        )
    except Exception as e:
        LOG_ERROR(e)
        raise

    else:
        return order
