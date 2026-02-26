import pytest

from dishka import AsyncContainer

from brain.application.interactors import CreateNoteInteractor, GetGraphInteractor, UpdateNoteInteractor
from brain.application.interactors.notes.dto import CreateNote, UpdateNote
from brain.domain.entities.user import User


async def seed_graph_data(
    dishka_request: AsyncContainer,
    user: User,
):
    create_interactor = await dishka_request.get(CreateNoteInteractor)

    alpha_id = await create_interactor.create_note(
        CreateNote(
            by_user_telegram_id=user.telegram_id,
            title="Alpha",
            text="links [[Beta]] and [[Orphan]]",
        )
    )
    beta_id = await create_interactor.create_note(
        CreateNote(
            by_user_telegram_id=user.telegram_id,
            title="Beta",
            text="see [[Gamma]]",
        )
    )
    gamma_id = await create_interactor.create_note(
        CreateNote(
            by_user_telegram_id=user.telegram_id,
            title="Gamma",
            text="",
        )
    )
    return alpha_id, beta_id, gamma_id


def node_ids(nodes):
    return {node.id for node in nodes}


def node_by_id(nodes):
    return {node.id: node for node in nodes}


def connection_tuples(connections):
    return {(c.from_id, c.to_id, c.kind) for c in connections}


@pytest.mark.asyncio
async def test_get_graph_without_query_returns_nodes_and_connections(
    dishka_request: AsyncContainer,
    user: User,
):
    alpha_id, beta_id, gamma_id = await seed_graph_data(dishka_request, user)
    interactor = await dishka_request.get(GetGraphInteractor)

    graph = await interactor.get_graph(user_id=user.id)

    expected_nodes = {
        f"note:{alpha_id}",
        f"note:{beta_id}",
        f"note:{gamma_id}",
        "keyword:Orphan",
    }
    assert node_ids(graph.nodes) == expected_nodes

    nodes = node_by_id(graph.nodes)
    assert nodes["keyword:Orphan"].has_keyword_note is False
    assert nodes[f"note:{alpha_id}"].represents_keyword is True
    assert nodes[f"note:{beta_id}"].represents_keyword is True

    expected_connections = {
        (f"note:{alpha_id}", "keyword:Orphan", "has_keyword"),
        (f"note:{alpha_id}", f"note:{beta_id}", "links_to"),
        (f"note:{beta_id}", f"note:{gamma_id}", "links_to"),
    }
    assert connection_tuples(graph.connections) == expected_connections


@pytest.mark.asyncio
async def test_get_graph_query_depth_limits_connected_nodes(
    dishka_request: AsyncContainer,
    user: User,
):
    alpha_id, beta_id, gamma_id = await seed_graph_data(dishka_request, user)
    interactor = await dishka_request.get(GetGraphInteractor)

    graph_depth_0 = await interactor.get_graph(
        user_id=user.id,
        query="Beta",
        depth=0,
    )
    assert node_ids(graph_depth_0.nodes) == {
        f"note:{beta_id}",
    }

    graph_depth_1 = await interactor.get_graph(
        user_id=user.id,
        query="Beta",
        depth=1,
    )
    assert "keyword:Orphan" not in node_ids(graph_depth_1.nodes)
    assert {
        f"note:{alpha_id}",
        f"note:{beta_id}",
        f"note:{gamma_id}",
    }.issubset(node_ids(graph_depth_1.nodes))

    graph_depth_2 = await interactor.get_graph(
        user_id=user.id,
        query="Beta",
        depth=2,
    )
    assert "keyword:Orphan" in node_ids(graph_depth_2.nodes)


@pytest.mark.asyncio
async def test_get_graph_query_returns_connected_nodes(
    dishka_request: AsyncContainer,
    user: User,
):
    alpha_id, beta_id, _ = await seed_graph_data(dishka_request, user)
    interactor = await dishka_request.get(GetGraphInteractor)

    graph = await interactor.get_graph(
        user_id=user.id,
        query="Orphan",
        depth=1,
    )

    assert node_ids(graph.nodes) == {
        "keyword:Orphan",
        f"note:{alpha_id}",
    }
    assert f"note:{beta_id}" not in node_ids(graph.nodes)


@pytest.mark.asyncio
async def test_get_graph_excludes_archived_notes(
    dishka_request: AsyncContainer,
    user: User,
):
    create_interactor = await dishka_request.get(CreateNoteInteractor)
    update_interactor = await dishka_request.get(UpdateNoteInteractor)
    graph_interactor = await dishka_request.get(GetGraphInteractor)

    archived_note_id = await create_interactor.create_note(
        CreateNote(
            by_user_telegram_id=user.telegram_id,
            title="ArchivedNode",
            text="Ref [[VisibleNode]]",
        ),
    )
    visible_note_id = await create_interactor.create_note(
        CreateNote(
            by_user_telegram_id=user.telegram_id,
            title="VisibleNode",
            text="Visible text",
        ),
    )

    await update_interactor.update_note(
        UpdateNote(
            note_id=archived_note_id,
            is_archived=True,
        ),
    )

    graph = await graph_interactor.get_graph(user_id=user.id)
    graph_node_ids = node_ids(graph.nodes)
    assert f"note:{archived_note_id}" not in graph_node_ids
    assert f"note:{visible_note_id}" in graph_node_ids
