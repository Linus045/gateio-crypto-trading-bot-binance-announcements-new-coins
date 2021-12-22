import re

import pytest
import requests
import requests_mock as req_mock

from gateio_new_coins_announcements_bot.new_listings_scraper import get_binance_announcement
from gateio_new_coins_announcements_bot.new_listings_scraper import get_kucoin_announcement
from gateio_new_coins_announcements_bot.new_listings_scraper import get_last_coin


def create_fake_announcement_object(title, use_kucoin_announcement_format=False):
    if use_kucoin_announcement_format is True:
        return {"items": [{"title": title}]}
    return {"data": {"catalogs": [{"articles": [{"title": title}]}]}}


class TestCase_latest_announcement:
    def test_latest_announcement_matches_title(self, mocker, fake_log):
        title = "Binance Will List Highstreet (HIGH)"

        with req_mock.Mocker() as m:
            m.get(req_mock.ANY, json=create_fake_announcement_object(title))
            assert get_binance_announcement() == title

    def test_latest_announcement_throws_when_get_request_excepts(self, mocker, fake_log):
        with req_mock.Mocker() as m:
            m.get(req_mock.ANY, exc=requests.exceptions.ConnectionError)
            with pytest.raises(requests.exceptions.ConnectionError):
                get_binance_announcement()

    @pytest.mark.skip("TODO: Get example error messages that could occur")
    def test_latest_announcement_throws_when_get_request_fails(self, mocker, fake_log):
        with req_mock.Mocker() as m:
            m.get(req_mock.ANY, status_code=400, json={})
            get_binance_announcement()


class TestCase_get_kucoin_announcement:
    def test_get_kucoin_announcement_matches_title(self, mocker, fake_log):
        title = "KuCoin Opens UnMarshal (MARSH) Deposit Service"
        with req_mock.Mocker() as m:
            m.get(req_mock.ANY, json=create_fake_announcement_object(title, use_kucoin_announcement_format=True))
            assert get_kucoin_announcement() == title

    def test_get_kucoin_announcement_throws_when_get_request_excepts(self, mocker, fake_log):
        with req_mock.Mocker() as m:
            m.get(req_mock.ANY, exc=requests.exceptions.ConnectionError)
            with pytest.raises(requests.exceptions.ConnectionError):
                get_kucoin_announcement()

    @pytest.mark.skip("TODO: Get example error messages that could occur")
    def test_get_kucoin_announcement_throws_when_get_request_fails(self, mocker, fake_log):
        with req_mock.Mocker() as m:
            m.get(req_mock.ANY, status_code=400, json={})
            get_kucoin_announcement()


class TestCase_get_last_coin:
    def test_get_last_coin_extracts_correctly_from_announcement(self, mocker, fake_log):
        title = "Binance Will List Highstreet (HIGH)"

        with req_mock.Mocker() as m:
            m.get(req_mock.ANY, json=create_fake_announcement_object(title))
            fake_config = {"TRADE_OPTIONS": {"KUCOIN_ANNOUNCEMENTS": False}}
            mocker.patch("gateio_new_coins_announcements_bot.new_listings_scraper.get_config", return_value=fake_config)
            assert get_last_coin() == "HIGH"

    def test_get_last_coin_returns_None_for_invalid_announement(self, mocker, fake_log):
        title = "Binance Futures Will List USDⓈ-M BTC & ETH Quarterly 0325 Futures Contracts"

        with req_mock.Mocker() as m:
            m.get(req_mock.ANY, json=create_fake_announcement_object(title))
            fake_config = {"TRADE_OPTIONS": {"KUCOIN_ANNOUNCEMENTS": False}}
            mocker.patch("gateio_new_coins_announcements_bot.new_listings_scraper.get_config", return_value=fake_config)
            assert get_last_coin() is None

    def test_get_last_coin_extracts_correctly_from_announcement_with_kucoin(self, mocker, fake_log):
        title = "Geeq (GEEQ) Gets Listed on KuCoin!"

        with req_mock.Mocker() as m:
            binance_matcher = re.compile(r"www\.binance")
            kucoin_matcher = re.compile(r"www\.kucoin")
            m.get(binance_matcher, json=create_fake_announcement_object(title))
            m.get(kucoin_matcher, json=create_fake_announcement_object(title, use_kucoin_announcement_format=True))

            fake_config = {"TRADE_OPTIONS": {"KUCOIN_ANNOUNCEMENTS": True}}
            mocker.patch("gateio_new_coins_announcements_bot.new_listings_scraper.get_config", return_value=fake_config)
            assert get_last_coin() == "GEEQ"

    def test_get_last_coin_returns_None_for_invalid_announement_with_kucoin(self, mocker, fake_log):
        title = (
            "Trade & Learn! Explore the Ethernity 2.0 Roadmap: 5,550 ERN To Be Shared! Rewards has been distributed!"
        )

        with req_mock.Mocker() as m:
            binance_matcher = re.compile(r"www\.binance")
            kucoin_matcher = re.compile(r"www\.kucoin")
            m.get(binance_matcher, json=create_fake_announcement_object(title))
            m.get(kucoin_matcher, json=create_fake_announcement_object(title, use_kucoin_announcement_format=True))

            fake_config = {"TRADE_OPTIONS": {"KUCOIN_ANNOUNCEMENTS": True}}
            mocker.patch("gateio_new_coins_announcements_bot.new_listings_scraper.get_config", return_value=fake_config)
            assert get_last_coin() is None
