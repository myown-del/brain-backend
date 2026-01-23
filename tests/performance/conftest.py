import logging
import time

import pytest

from tests.integration.api.conftest import api_client, notes_app
from tests.integration.conftest import (
    alembic_config,
    dishka,
    dishka_request,
    repo_hub,
    upgrade_schema_db,
    user,
)

logger = logging.getLogger()

__all__ = [
    "alembic_config",
    "api_client",
    "dishka",
    "dishka_request",
    "notes_app",
    "repo_hub",
    "upgrade_schema_db",
    "user",
]


@pytest.fixture(autouse=True)
def log_performance_test_duration(request: pytest.FixtureRequest) -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    for handler in root_logger.handlers:
        handler.setLevel(logging.INFO)
    start = time.perf_counter()
    yield
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "Performance test finished: %s in %.2f ms",
        request.node.nodeid,
        elapsed_ms,
    )


def pytest_configure(config: pytest.Config) -> None:
    config.option.log_cli = True
    config.option.log_cli_level = "INFO"


@pytest.fixture(scope="session", autouse=True)
def ensure_performance_logging() -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    for handler in root_logger.handlers:
        handler.setLevel(logging.INFO)
