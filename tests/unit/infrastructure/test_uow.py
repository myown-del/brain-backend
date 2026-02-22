from unittest.mock import AsyncMock, Mock

import pytest
from neo4j import AsyncDriver
from sqlalchemy.ext.asyncio import AsyncSession

from brain.infrastructure.uow.backends import (
    ITransactionController,
    Neo4jTransactionController,
    SqlAlchemyTransactionController,
)
from brain.infrastructure.uow.composite import CompositeUnitOfWork
from brain.infrastructure.uow.context import UnitOfWorkContext


def _make_mock_controller(key: str) -> ITransactionController:
    controller = Mock()
    controller.backend_key = key
    controller.begin = AsyncMock()
    controller.ensure_started = AsyncMock()
    controller.commit = AsyncMock()
    controller.rollback = AsyncMock()
    controller.close = AsyncMock()
    return controller


@pytest.mark.asyncio
async def test_uow_supports_multiple_controllers_and_commit_order() -> None:
    c1 = _make_mock_controller("c1")
    c2 = _make_mock_controller("c2")
    c3 = _make_mock_controller("c3")
    context = UnitOfWorkContext()
    uow = CompositeUnitOfWork(
        controllers=[c1, c2, c3],
        uow_context=context,
    )

    async with uow:
        await uow.commit()

    c1.begin.assert_awaited_once_with(context)
    c2.begin.assert_awaited_once_with(context)
    c3.begin.assert_awaited_once_with(context)
    assert [c.args[0] for c in c1.commit.await_args_list] == [context]
    assert [c.args[0] for c in c2.commit.await_args_list] == [context]
    assert [c.args[0] for c in c3.commit.await_args_list] == [context]
    c3.close.assert_awaited_once_with(context)
    c2.close.assert_awaited_once_with(context)
    c1.close.assert_awaited_once_with(context)


@pytest.mark.asyncio
async def test_uow_rollback_order_is_reverse() -> None:
    c1 = _make_mock_controller("c1")
    c2 = _make_mock_controller("c2")
    c3 = _make_mock_controller("c3")
    context = UnitOfWorkContext()
    uow = CompositeUnitOfWork(
        controllers=[c1, c2, c3],
        uow_context=context,
    )

    async with uow:
        await uow.rollback()

    assert c3.rollback.await_count == 1
    assert c2.rollback.await_count == 1
    assert c1.rollback.await_count == 1
    assert c3.close.await_count == 1
    assert c2.close.await_count == 1
    assert c1.close.await_count == 1


@pytest.mark.asyncio
async def test_uow_rolls_back_on_exception_only() -> None:
    c1 = _make_mock_controller("c1")
    c2 = _make_mock_controller("c2")
    context = UnitOfWorkContext()
    uow = CompositeUnitOfWork(
        controllers=[c1, c2],
        uow_context=context,
    )

    with pytest.raises(RuntimeError, match="fail"):
        async with uow:
            raise RuntimeError("fail")

    c2.rollback.assert_awaited_once_with(context)
    c1.rollback.assert_awaited_once_with(context)

    c1.rollback.reset_mock()
    c2.rollback.reset_mock()
    async with uow:
        pass
    c1.rollback.assert_not_awaited()
    c2.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_uow_flush_delegates_only_to_primary_controller() -> None:
    sql = _make_mock_controller("sql")
    sql.flush = AsyncMock()
    neo = _make_mock_controller("neo4j")
    neo.flush = AsyncMock()
    context = UnitOfWorkContext()
    uow = CompositeUnitOfWork(
        controllers=[sql, neo],
        uow_context=context,
        primary_flush_controller_key="sql",
    )

    async with uow:
        await uow.flush()

    sql.flush.assert_awaited_once_with(context)
    neo.flush.assert_not_awaited()


@pytest.mark.asyncio
async def test_uow_commit_and_rollback_are_idempotent() -> None:
    c1 = _make_mock_controller("c1")
    context = UnitOfWorkContext()
    uow = CompositeUnitOfWork(
        controllers=[c1],
        uow_context=context,
    )

    async with uow:
        await uow.commit()
        await uow.commit()
        await uow.rollback()

    c1.commit.assert_awaited_once_with(context)
    c1.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_sql_controller_lifecycle_and_flush() -> None:
    session = AsyncMock(spec=AsyncSession)
    context = UnitOfWorkContext()
    controller = SqlAlchemyTransactionController(session=session)

    await controller.begin(context)
    await controller.flush(context)
    await controller.commit(context)
    await controller.rollback(context)
    await controller.close(context)

    assert context.is_started("sql") is True
    assert context.get_handle("sql") is session
    session.flush.assert_awaited_once()
    session.commit.assert_awaited_once()
    session.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_neo4j_controller_lazy_start_and_handles() -> None:
    driver = Mock(spec=AsyncDriver)
    neo4j_session = AsyncMock()
    neo4j_tx = AsyncMock()
    neo4j_session.begin_transaction = AsyncMock(return_value=neo4j_tx)
    driver.session.return_value = neo4j_session
    context = UnitOfWorkContext()
    controller = Neo4jTransactionController(
        driver=driver,
        database="neo4j",
    )

    await controller.begin(context)
    assert context.is_started("neo4j") is False

    await controller.ensure_started(context)
    assert context.is_started("neo4j") is True
    assert context.get_handle("neo4j") is neo4j_tx
    assert context.get_handle("neo4j_session") is neo4j_session

    await controller.commit(context)
    await controller.rollback(context)
    await controller.close(context)

    driver.session.assert_called_once_with(database="neo4j")
    neo4j_session.begin_transaction.assert_awaited_once()
    neo4j_tx.commit.assert_awaited_once()
    neo4j_tx.rollback.assert_awaited_once()
    neo4j_session.close.assert_awaited_once()
