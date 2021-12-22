import logging

import pytest
from _pytest.mark import param


@pytest.fixture(scope="function", autouse=True)
def fake_log(mocker, caplog):
    print("INITIALIZING LOGGER")
    caplog.set_level(logging.NOTSET)

    # This replaces the log function every LOG_* function calls, see gateio_new_coins_announcements_bot.logger
    # To see the output run test using:
    #   pytest --log-cli-level <LOG_LEVEL>
    #   (for LOG_LEVEL see https://docs.python.org/3/library/logging.html#levels)
    # or activate it inside pyproject.toml -> see [tool.pytest.ini_options] header
    # More info: https://docs.pytest.org/en/6.2.x/capture.html
    class FakeLogger:
        def __init__(self) -> None:
            self.logger = logging.getLogger(__name__)

        def log(self, log_level, *args, extra=None):
            msg = f"EXTRA: {extra}\nLOG_MESSAGE: {str(*args)}"
            self.logger.log(log_level, msg)

    fake_logger = FakeLogger()
    mocker.patch("gateio_new_coins_announcements_bot.logger._logger", new=fake_logger)
    yield param
    print("TEARDOWN TEST")
