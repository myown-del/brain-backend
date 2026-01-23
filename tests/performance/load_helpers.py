from __future__ import annotations

import asyncio
import os
from collections.abc import Awaitable, Callable
from typing import TypeVar

ResultT = TypeVar("ResultT")


def load_load_test_settings() -> tuple[int, int]:
    total = int(os.getenv(key="LOAD_TEST_NOTES_TOTAL", default="40"))
    concurrency = int(os.getenv(key="LOAD_TEST_NOTES_CONCURRENCY", default="10"))
    safe_concurrency = max(1, min(total, concurrency))
    safe_total = max(1, total)
    return safe_total, safe_concurrency


async def run_concurrent_tasks(
    total: int,
    concurrency: int,
    worker: Callable[[int], Awaitable[ResultT]],
) -> list[ResultT]:
    semaphore = asyncio.Semaphore(concurrency)

    async def _guarded(index: int) -> ResultT:
        async with semaphore:
            return await worker(index)

    tasks = [asyncio.create_task(_guarded(index=index)) for index in range(total)]
    return list(await asyncio.gather(*tasks))
