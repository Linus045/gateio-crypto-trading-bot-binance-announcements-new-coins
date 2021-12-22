import pytest
import requests
import requests_mock as req_mock

from gateio_new_coins_announcements_bot.new_listings_scraper import get_announcement


def test_latest_announcement_matches_title(mocker, fake_log):
    title = "Binance Will List Highstreet (HIGH)"

    def create_fake_announcement_object(title):
        return {"data": {"catalogs": [{"articles": [{"title": title}]}]}}

    with req_mock.Mocker() as m:
        m.get(req_mock.ANY, json=create_fake_announcement_object(title))
        assert get_announcement() == title


def test_latest_announcement_throws_when_get_request_excepts(mocker, fake_log):
    with req_mock.Mocker() as m:
        m.get(req_mock.ANY, exc=requests.exceptions.ConnectionError)
        with pytest.raises(requests.exceptions.ConnectionError):
            get_announcement()


@pytest.mark.skip("TODO: Get example error messages that could occur")
def test_latest_announcement_throws_when_get_request_fails(mocker, fake_log):
    with req_mock.Mocker() as m:
        m.get(req_mock.ANY, status_code=400, json={})
        get_announcement()
