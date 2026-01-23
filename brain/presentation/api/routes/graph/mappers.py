from brain.domain.entities.graph import GraphData, GraphNode, GraphConnection
from brain.presentation.api.routes.graph.models import (
    GraphSchema,
    GraphNodeSchema,
    GraphConnectionSchema,
    GraphNodeKindEnum,
    GraphNodeNoteSchema,
    GraphNodeKeywordSchema,
)


def map_graph_node_to_schema(node: GraphNode) -> GraphNodeSchema:
    if node.kind == GraphNodeKindEnum.KEYWORD.value:
        return GraphNodeKeywordSchema(
            id=node.id,
            type=GraphNodeKindEnum.KEYWORD,
            title=node.title,
        )

    return GraphNodeNoteSchema(
        id=node.id,
        type=GraphNodeKindEnum.NOTE,
        title=node.title,
        represents_keyword=node.represents_keyword,
    )


def map_graph_connection_to_schema(
    connection: GraphConnection,
) -> GraphConnectionSchema:
    return GraphConnectionSchema(
        from_id=connection.from_id,
        to_id=connection.to_id,
        kind=connection.kind,
    )


def map_graph_to_schema(graph: GraphData) -> GraphSchema:
    return GraphSchema(
        nodes=[map_graph_node_to_schema(node) for node in graph.nodes],
        connections=[map_graph_connection_to_schema(connection) for connection in graph.connections],
    )
