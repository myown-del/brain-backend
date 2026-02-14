from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, HTTPException, Query
from pytz import timezone as pytz_timezone, UnknownTimeZoneError
from starlette import status

from brain.application.interactors import (
    CreateDraftInteractor,
    DeleteDraftInteractor,
    GetDraftInteractor,
    GetDraftCreationStatsInteractor,
    GetDraftsInteractor,
    SearchDraftsByTextInteractor,
    UpdateDraftInteractor,
)
from brain.application.interactors.drafts.exceptions import (
    DraftNotFoundException,
    DraftPatchApplyException,
)
from brain.domain.entities.user import User
from brain.presentation.api.dependencies.auth import get_notes_user_from_request
from brain.presentation.api.routes.drafts.mappers import (
    map_create_schema_to_dto,
    map_draft_creation_stat_to_schema,
    map_draft_to_read_schema,
    map_update_schema_to_dto,
)
from brain.presentation.api.routes.drafts.models import (
    CreateDraftSchema,
    DraftCreationStatSchema,
    ReadDraftSchema,
    SearchDraftsSchema,
    UpdateDraftSchema,
)


@inject
async def get_drafts(
    interactor: FromDishka[GetDraftsInteractor],
    user: User = Depends(get_notes_user_from_request),
):
    drafts = await interactor.get_drafts(user_id=user.id)
    return [map_draft_to_read_schema(draft) for draft in drafts]


@inject
async def search_drafts(
    get_interactor: FromDishka[GetDraftsInteractor],
    search_interactor: FromDishka[SearchDraftsByTextInteractor],
    body: SearchDraftsSchema,
    user: User = Depends(get_notes_user_from_request),
):
    if body.text_query:
        drafts = await search_interactor.search(
            user_id=user.id,
            query=body.text_query,
            from_date=body.from_date,
            to_date=body.to_date,
            hashtags=body.hashtags,
        )
    else:
        drafts = await get_interactor.get_drafts(
            user_id=user.id,
            from_date=body.from_date,
            to_date=body.to_date,
            hashtags=body.hashtags,
        )
    return [map_draft_to_read_schema(draft) for draft in drafts]


@inject
async def create_draft(
    create_interactor: FromDishka[CreateDraftInteractor],
    get_interactor: FromDishka[GetDraftInteractor],
    draft: CreateDraftSchema,
    user: User = Depends(get_notes_user_from_request),
):
    draft_id = await create_interactor.create_draft(
        map_create_schema_to_dto(schema=draft, user=user),
    )
    created_draft = await get_interactor.get_draft_by_id(draft_id)
    if created_draft is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found",
        )
    return map_draft_to_read_schema(created_draft)


@inject
async def delete_draft(
    get_interactor: FromDishka[GetDraftInteractor],
    delete_interactor: FromDishka[DeleteDraftInteractor],
    draft_id: UUID,
    user: User = Depends(get_notes_user_from_request),
):
    draft = await get_interactor.get_draft_by_id(draft_id)
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found",
        )
    if draft.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )
    try:
        await delete_interactor.delete_draft(draft_id)
    except DraftNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found",
        )


@inject
async def update_draft(
    get_interactor: FromDishka[GetDraftInteractor],
    update_interactor: FromDishka[UpdateDraftInteractor],
    draft_id: UUID,
    draft: UpdateDraftSchema,
    user: User = Depends(get_notes_user_from_request),
):
    existing_draft = await get_interactor.get_draft_by_id(draft_id)
    if not existing_draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found",
        )
    if existing_draft.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )

    try:
        updated_draft = await update_interactor.update_draft(
            map_update_schema_to_dto(
                draft_id=draft_id,
                schema=draft,
            ),
        )
    except DraftNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found",
        )
    except DraftPatchApplyException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to apply patch",
        )

    return map_draft_to_read_schema(updated_draft)


@inject
async def get_draft_creation_stats(
    interactor: FromDishka[GetDraftCreationStatsInteractor],
    timezone: str = Query("UTC"),
    user: User = Depends(get_notes_user_from_request),
):
    try:
        pytz_timezone(timezone)
    except UnknownTimeZoneError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid timezone",
        )
    stats = await interactor.get_stats(
        user_id=user.id,
        timezone_name=timezone,
    )
    return [map_draft_creation_stat_to_schema(stat) for stat in stats]


def get_router() -> APIRouter:
    router = APIRouter(prefix="/drafts")
    router.add_api_route(
        path="",
        endpoint=get_drafts,
        methods=["GET"],
        response_model=list[ReadDraftSchema],
        summary="Get all drafts",
        status_code=status.HTTP_200_OK,
    )
    router.add_api_route(
        path="/search",
        endpoint=search_drafts,
        methods=["POST"],
        response_model=list[ReadDraftSchema],
        summary="Search drafts with filters",
        status_code=status.HTTP_200_OK,
    )
    router.add_api_route(
        path="/creation-stats",
        endpoint=get_draft_creation_stats,
        methods=["GET"],
        response_model=list[DraftCreationStatSchema],
        summary="Get draft creation stats by date",
        status_code=status.HTTP_200_OK,
    )
    router.add_api_route(
        path="",
        endpoint=create_draft,
        methods=["POST"],
        response_model=ReadDraftSchema,
        summary="Create draft",
        status_code=status.HTTP_201_CREATED,
    )
    router.add_api_route(
        path="/{draft_id}",
        endpoint=delete_draft,
        methods=["DELETE"],
        summary="Delete draft",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    router.add_api_route(
        path="/{draft_id}",
        endpoint=update_draft,
        methods=["PATCH"],
        response_model=ReadDraftSchema,
        summary="Update draft",
        status_code=status.HTTP_200_OK,
    )
    return router
