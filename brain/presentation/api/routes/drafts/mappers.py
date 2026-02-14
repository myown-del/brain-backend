from dataclasses import asdict
from uuid import UUID

from brain.application.interactors.drafts.dto import CreateDraft, UpdateDraft
from brain.application.abstractions.repositories.models import DraftCreationStat
from brain.application.types import Unset
from brain.domain.entities.draft import Draft
from brain.domain.entities.user import User
from brain.presentation.api.routes.drafts.models import (
    CreateDraftSchema,
    DraftCreationStatSchema,
    ReadDraftSchema,
    UpdateDraftSchema,
)


def map_draft_to_read_schema(draft: Draft) -> ReadDraftSchema:
    return ReadDraftSchema.model_validate(asdict(draft))


def map_create_schema_to_dto(
    schema: CreateDraftSchema,
    user: User,
) -> CreateDraft:
    return CreateDraft(
        user_id=user.id,
        text=schema.text,
    )


def map_update_schema_to_dto(
    draft_id: UUID,
    schema: UpdateDraftSchema,
) -> UpdateDraft:
    payload = schema.model_dump(exclude_unset=True)
    return UpdateDraft(
        draft_id=draft_id,
        text=payload.get("text", Unset),
        patch=payload.get("patch", Unset),
    )


def map_draft_creation_stat_to_schema(
    stat: DraftCreationStat,
) -> DraftCreationStatSchema:
    return DraftCreationStatSchema.model_validate(asdict(stat))
