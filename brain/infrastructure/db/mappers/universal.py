from typing import Type

from adaptix.conversion import get_converter

from brain.domain.entities.common import EntityT
from brain.infrastructure.db.models.base import SqlAlchemyModelT


def from_entity_to_db(entity: EntityT, db_cls: Type[SqlAlchemyModelT]) -> SqlAlchemyModelT:
    source_cls = type(entity)
    converter = get_converter(source_cls, db_cls)
    try:
        return converter(entity)
    except Exception as e:
        raise ValueError(f"Failed to convert {source_cls} to {db_cls}") from e


def from_db_to_entity(db_model: SqlAlchemyModelT, entity_cls: Type[EntityT]) -> EntityT:
    source_cls = type(db_model)
    converter = get_converter(source_cls, entity_cls)
    try:
        return converter(db_model)
    except Exception as e:
        raise ValueError(f"Failed to convert {source_cls} to {entity_cls}") from e
