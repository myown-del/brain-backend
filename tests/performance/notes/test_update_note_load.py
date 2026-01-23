import logging
import time

import pytest
from fastapi import FastAPI
from starlette import status

from brain.domain.entities.note import Note
from brain.domain.entities.user import User
from brain.infrastructure.db.repositories.hub import RepositoryHub
from tests.integration.api.conftest import ApiClientFactory
from tests.integration.api.notes.helpers import create_keyword_note
from tests.performance.load_helpers import (
    load_load_test_settings,
    run_concurrent_tasks,
)

logger = logging.getLogger()


@pytest.mark.asyncio
async def test_load_update_notes(
    notes_app: FastAPI,
    api_client: ApiClientFactory,
    repo_hub: RepositoryHub,
    user: User,
) -> None:
    # setup: create notes to update via API
    total, concurrency = load_load_test_settings()
    notes: list[Note] = []
    for index in range(total):
        note = await create_keyword_note(
            repo_hub=repo_hub,
            user=user,
            title=f"Load Update {index}",
            text=f"Body {index}",
        )
        notes.append(note)

    async with api_client(notes_app) as client:
        # action: send concurrent update requests
        async def _update_note(index: int) -> tuple[int, str]:
            response = await client.request(
                method="PATCH",
                url=f"/api/notes/{notes[index].id}",
                json={"title": f"Updated {index}"},
            )
            return response.status_code, response.json()["title"]

        start = time.perf_counter()
        responses = await run_concurrent_tasks(
            total=total,
            concurrency=concurrency,
            worker=_update_note,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

    # check: all responses are ok and notes updated in db
    assert all(status_code == status.HTTP_200_OK for status_code, _ in responses)
    for index, note in enumerate(notes):
        stored_note = await repo_hub.notes.get_by_id(note_id=note.id)
        assert stored_note is not None
        assert stored_note.title == f"Updated {index}"
    logger.info(
        "Update load metrics: total=%d concurrency=%d elapsed_ms=%.2f rps=%.2f",
        total,
        concurrency,
        elapsed_ms,
        total / (elapsed_ms / 1000) if elapsed_ms > 0 else 0.0,
    )
