from dataclasses import asdict
from uuid import UUID

from brain.application.interactors.drafts.dto import CreateDraft, UpdateDraft
from brain.application.abstractions.repositories.models import DraftCreationStat
from brain.config.models import S3Config
from brain.application.types import Unset
from brain.domain.entities.draft import Draft
from brain.domain.entities.user import User
from brain.domain.services.media import build_public_file_url
from brain.presentation.api.routes.drafts.models import (
    CreateDraftSchema,
    DraftCreationStatSchema,
    ReadDraftSchema,
    UpdateDraftSchema,
)
from brain.presentation.api.routes.users.models import ReadS3FileSchema


def map_draft_to_read_schema(draft: Draft, s3_config: S3Config) -> ReadDraftSchema:
    file_schema: ReadS3FileSchema | None = None
    if draft.file is not None:
        file_schema = ReadS3FileSchema(
            id=draft.file.id,
            name=draft.file.name,
            path=draft.file.path,
            url=build_public_file_url(
                external_host=s3_config.external_host,
                file_path=draft.file.path,
            ),
            content_type=draft.file.content_type,
            created_at=draft.file.created_at,
        )

    return ReadDraftSchema(
        id=draft.id,
        text=draft.text,
        file=file_schema,
        hashtags=draft.hashtags,
        created_at=draft.created_at,
        updated_at=draft.updated_at,
    )


def map_create_schema_to_dto(
    schema: CreateDraftSchema,
    user: User,
) -> CreateDraft:
    return CreateDraft(
        user_id=user.id,
        text=schema.text,
        file_id=schema.file_id,
    )


def map_update_schema_to_dto(
    draft_id: UUID,
    schema: UpdateDraftSchema,
) -> UpdateDraft:
    payload = schema.model_dump(exclude_unset=True)
    return UpdateDraft(
        draft_id=draft_id,
        text=payload.get("text", Unset),
        file_id=payload.get("file_id", Unset),
        patch=payload.get("patch", Unset),
    )


def map_draft_creation_stat_to_schema(
    stat: DraftCreationStat,
) -> DraftCreationStatSchema:
    return DraftCreationStatSchema.model_validate(asdict(stat))
