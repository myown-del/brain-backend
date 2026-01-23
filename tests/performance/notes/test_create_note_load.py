import logging
import time

import pytest
from fastapi import FastAPI
from starlette import status

from brain.domain.entities.user import User
from brain.infrastructure.db.repositories.hub import RepositoryHub
from tests.integration.api.conftest import ApiClientFactory
from tests.performance.load_helpers import (
    load_load_test_settings,
    run_concurrent_tasks,
)

logger = logging.getLogger()


@pytest.mark.asyncio
async def test_load_create_notes(
    notes_app: FastAPI,
    api_client: ApiClientFactory,
    repo_hub: RepositoryHub,
    user: User,
) -> None:
    # setup: prepare payloads for concurrent creation
    total, concurrency = load_load_test_settings()
    payloads = [
        {"title": f"Load Create {index}", "text": f"Body {index}"}
        for index in range(total)
    ]

    async with api_client(notes_app) as client:
        # action: send concurrent create requests
        async def _create_note(index: int) -> tuple[int, str]:
            response = await client.request(
                method="POST",
                url="/api/notes",
                json=payloads[index],
            )
            return response.status_code, response.json()["title"]

        start = time.perf_counter()
        responses = await run_concurrent_tasks(
            total=total,
            concurrency=concurrency,
            worker=_create_note,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

    # check: all responses are created and notes exist in db
    assert all(status_code == status.HTTP_201_CREATED for status_code, _ in responses)
    stored_notes = await repo_hub.notes.get_by_user_telegram_id(
        telegram_id=user.telegram_id,
    )
    assert len(stored_notes) == total
    logger.info(
        "Create load metrics: total=%d concurrency=%d elapsed_ms=%.2f rps=%.2f",
        total,
        concurrency,
        elapsed_ms,
        total / (elapsed_ms / 1000) if elapsed_ms > 0 else 0.0,
    )
