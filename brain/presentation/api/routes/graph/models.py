from enum import Enum
from typing import Literal, TypeAlias

from pydantic import BaseModel


class GraphNodeKindEnum(str, Enum):
    NOTE = "note"
    KEYWORD = "keyword"


class GraphNodeNoteSchema(BaseModel):
    id: str
    type: Literal[GraphNodeKindEnum.NOTE]
    title: str
    represents_keyword: bool | None = None


class GraphNodeKeywordSchema(BaseModel):
    id: str
    type: Literal[GraphNodeKindEnum.KEYWORD]
    title: str


class GraphConnectionSchema(BaseModel):
    from_id: str
    to_id: str
    kind: str


GraphNodeSchema: TypeAlias = GraphNodeNoteSchema | GraphNodeKeywordSchema


class GraphSchema(BaseModel):
    nodes: list[GraphNodeSchema]
    connections: list[GraphConnectionSchema]
