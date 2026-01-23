import logging
import os
import time
from collections.abc import Callable
from dataclasses import dataclass

import pytest
from fastapi import FastAPI
from starlette import status

from brain.domain.entities.user import User
from brain.infrastructure.db.repositories.hub import RepositoryHub
from tests.integration.api.conftest import ApiClientFactory
from tests.integration.api.notes.helpers import create_keyword_note

logger = logging.getLogger()


def load_perf_threshold_ms(*, env_key: str, default_ms: int) -> int:
    return int(os.getenv(key=env_key, default=str(default_ms)))


def build_large_text(*, size: int, wikilinks: list[str]) -> str:
    base = "lorem ipsum "
    parts: list[str] = []
    for link in wikilinks:
        parts.append(base)
        parts.append(f"[[{link}]]")
    text = "".join(parts)
    if len(text) > size:
        raise ValueError("Requested size is too small for wikilinks")
    text += "x" * (size - len(text))
    return text


@pytest.mark.asyncio
@pytest.mark.parametrize("size", [10_000, 50_000, 100_000])
async def test_create_large_note_response_time(
    size: int,
    notes_app: FastAPI,
    api_client: ApiClientFactory,
    repo_hub: RepositoryHub,
    user: User,
) -> None:
    # setup: prepare a large note payload
    max_ms = load_perf_threshold_ms(
        env_key="PERF_MAX_CREATE_NOTE_MS",
        default_ms=10_000,
    )
    payload = {
        "title": f"Large Note {size}",
        "text": build_large_text(size=size, wikilinks=["Alpha", "Beta"]),
    }

    # action: create the note and measure response time
    async with api_client(notes_app) as client:
        start = time.perf_counter()
        response = await client.request(
            method="POST",
            url="/api/notes",
            json=payload,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

    # check: response is ok, note persisted, and time under threshold
    assert response.status_code == status.HTTP_201_CREATED
    stored = await repo_hub.notes.get_by_title(
        user_id=user.id,
        title=payload["title"],
        exact_match=True,
    )
    assert stored is not None
    assert stored.text is not None
    assert len(stored.text) == size
    assert elapsed_ms <= max_ms
    logger.info(
        "Create large note metrics: size=%d elapsed_ms=%.2f threshold_ms=%d",
        size,
        elapsed_ms,
        max_ms,
    )


@dataclass(frozen=True)
class UpdateScenario:
    name: str
    modifier: Callable[[str], str]
    env_key: str
    default_ms: int


def edit_without_touching_wikilinks(text: str) -> str:
    return text[:-200] + ("y" * 200)


def edit_touching_some_wikilinks(text: str) -> str:
    return text.replace("[[Beta]]", "[[BetaUpdated]]", 1)


def edit_large_block(text: str) -> str:
    start = len(text) // 3
    end = start + 5_000
    replacement = "z" * (end - start)
    return text[:start] + replacement + text[end:]


def edit_multiple_small_blocks(text: str) -> str:
    indices = [1_000, 5_000, 9_000, 12_000]
    chars = list(text)
    for index in indices:
        if index < len(chars):
            chars[index : index + 10] = list("small_edit")
    return "".join(chars)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "scenario",
    [
        UpdateScenario(
            name="no_wikilink_touch",
            modifier=edit_without_touching_wikilinks,
            env_key="PERF_MAX_UPDATE_NOTE_NO_WIKILINK_MS",
            default_ms=10_000,
        ),
        UpdateScenario(
            name="touch_wikilinks",
            modifier=edit_touching_some_wikilinks,
            env_key="PERF_MAX_UPDATE_NOTE_TOUCH_WIKILINK_MS",
            default_ms=12_000,
        ),
        UpdateScenario(
            name="large_block",
            modifier=edit_large_block,
            env_key="PERF_MAX_UPDATE_NOTE_LARGE_BLOCK_MS",
            default_ms=12_000,
        ),
        UpdateScenario(
            name="multiple_small_blocks",
            modifier=edit_multiple_small_blocks,
            env_key="PERF_MAX_UPDATE_NOTE_SMALL_BLOCKS_MS",
            default_ms=12_000,
        ),
    ],
)
async def test_update_large_note_response_time(
    scenario: UpdateScenario,
    notes_app: FastAPI,
    api_client: ApiClientFactory,
    repo_hub: RepositoryHub,
    user: User,
) -> None:
    # setup: create a large note to update
    size = 80_000
    initial_text = build_large_text(
        size=size,
        wikilinks=["Alpha", "Beta", "Gamma"],
    )
    note = await create_keyword_note(
        repo_hub=repo_hub,
        user=user,
        title=f"Update Large {scenario.name}",
        text=initial_text,
    )
    updated_text = scenario.modifier(initial_text)
    max_ms = load_perf_threshold_ms(
        env_key=scenario.env_key,
        default_ms=scenario.default_ms,
    )

    # action: update the note and measure response time
    async with api_client(notes_app) as client:
        start = time.perf_counter()
        response = await client.request(
            method="PATCH",
            url=f"/api/notes/{note.id}",
            json={"text": updated_text},
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

    # check: response ok, note updated, time under threshold
    assert response.status_code == status.HTTP_200_OK
    stored = await repo_hub.notes.get_by_id(note_id=note.id)
    assert stored is not None
    assert stored.text == updated_text
    assert elapsed_ms <= max_ms
    logger.info(
        "Update large note metrics: scenario=%s size=%d elapsed_ms=%.2f threshold_ms=%d",
        scenario.name,
        len(updated_text),
        elapsed_ms,
        max_ms,
    )
