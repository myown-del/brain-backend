from datetime import datetime
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import Depends, APIRouter, HTTPException, Query, Response, UploadFile, File
from starlette import status

from brain.application.interactors import (
    CreateNoteInteractor,
    DeleteNoteInteractor,
    GetNoteInteractor,
    GetNoteCreationStatsInteractor,
    GetNotesInteractor,
    SearchNotesByTitleInteractor,
    SearchWikilinkSuggestionsInteractor,
    UpdateNoteInteractor,
    ExportNotesInteractor,
    GetNewNoteTitleInteractor,
    ImportNotesInteractor,
)
from brain.application.interactors.notes.exceptions import (
    NoteNotFoundException,
    KeywordNotFoundException,
    NoteTitleAlreadyExistsException,
    NoteTitleRequiredException,
)
from brain.domain.entities.user import User
from brain.presentation.api.dependencies.auth import get_notes_user_from_request
from brain.presentation.api.routes.notes.mappers import (
    map_create_schema_to_dto,
    map_note_to_read_schema,
    map_update_schema_to_dto,
    map_wikilink_suggestion_to_schema,
    map_note_creation_stat_to_schema,
)
from brain.presentation.api.routes.notes.models import (
    ReadNoteSchema,
    CreateNoteSchema,
    UpdateNoteSchema,
    WikilinkSuggestionSchema,
    NoteCreationStatSchema,
    NewNoteTitleSchema,
)


@inject
async def get_notes(
    interactor: FromDishka[GetNotesInteractor],
    from_date: datetime | None = Query(None),
    to_date: datetime | None = Query(None),
    user: User = Depends(get_notes_user_from_request),
):
    notes = await interactor.get_notes(
        user.telegram_id,
        from_date=from_date,
        to_date=to_date,
    )
    return [map_note_to_read_schema(note) for note in notes]


@inject
async def get_wikilink_suggestions(
    interactor: FromDishka[SearchWikilinkSuggestionsInteractor],
    query: str = Query(..., min_length=1),
    user: User = Depends(get_notes_user_from_request),
):
    suggestions = await interactor.search_wikilink_suggestions(
        user_id=user.id,
        query=query,
    )
    return [map_wikilink_suggestion_to_schema(suggestion) for suggestion in suggestions]


@inject
async def search_notes_by_title(
    interactor: FromDishka[SearchNotesByTitleInteractor],
    query: str = Query(..., min_length=1),
    exact_match: bool = Query(False),
    user: User = Depends(get_notes_user_from_request),
):
    notes = await interactor.search(
        user_id=user.id,
        query=query,
        exact_match=exact_match,
    )
    return [map_note_to_read_schema(note) for note in notes]


@inject
async def create_note(
    create_interactor: FromDishka[CreateNoteInteractor],
    get_note_interactor: FromDishka[GetNoteInteractor],
    note: CreateNoteSchema,
    user: User = Depends(get_notes_user_from_request),
):
    data = map_create_schema_to_dto(note, user)
    try:
        note_id = await create_interactor.create_note(data)
    except NoteTitleRequiredException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Note title cannot be null",
        )
    except NoteTitleAlreadyExistsException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Note title must be unique",
        )
    except KeywordNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Keyword not found",
        )
    note = await get_note_interactor.get_note_by_id(note_id)
    return map_note_to_read_schema(note)


@inject
async def delete_note(
    get_note_interactor: FromDishka[GetNoteInteractor],
    delete_interactor: FromDishka[DeleteNoteInteractor],
    note_id: UUID,
    user: User = Depends(get_notes_user_from_request),
):
    note = await get_note_interactor.get_note_by_id(note_id)
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    if note.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )

    try:
        await delete_interactor.delete_note(note_id)
    except NoteNotFoundException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")


@inject
async def update_note(
    get_note_interactor: FromDishka[GetNoteInteractor],
    update_interactor: FromDishka[UpdateNoteInteractor],
    note_id: UUID,
    note: UpdateNoteSchema,
    user: User = Depends(get_notes_user_from_request),
):
    existing_note = await get_note_interactor.get_note_by_id(note_id)
    if not existing_note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    if existing_note.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )

    data = map_update_schema_to_dto(note_id, note)

    try:
        updated_note = await update_interactor.update_note(data)
    except NoteNotFoundException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    except NoteTitleRequiredException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Note title cannot be null",
        )
    except NoteTitleAlreadyExistsException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Note title must be unique",
        )
    except KeywordNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Keyword not found",
        )

    return map_note_to_read_schema(updated_note)


@inject
async def export_notes(
    interactor: FromDishka[ExportNotesInteractor],
    user: User = Depends(get_notes_user_from_request),
):
    zip_bytes = await interactor.export_notes(user.telegram_id)
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=notes_export.zip"},
    )


@inject
async def import_notes(
    interactor: FromDishka[ImportNotesInteractor],
    file: UploadFile = File(...),
    user: User = Depends(get_notes_user_from_request),
):
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="File must be a .zip extension")

    content = await file.read()
    try:
        await interactor.import_notes(user.telegram_id, content)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid zip file")

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@inject
async def get_note_creation_stats(
    interactor: FromDishka[GetNoteCreationStatsInteractor],
    user: User = Depends(get_notes_user_from_request),
):
    stats = await interactor.get_stats(user.telegram_id)
    return [map_note_creation_stat_to_schema(stat) for stat in stats]


@inject
async def get_new_note_title(
    interactor: FromDishka[GetNewNoteTitleInteractor],
    user: User = Depends(get_notes_user_from_request),
):
    title = await interactor.get_title(user.id)
    return NewNoteTitleSchema(title=title)


def get_router() -> APIRouter:
    router = APIRouter(prefix="/notes")
    router.add_api_route(
        path="",
        endpoint=get_notes,
        methods=["GET"],
        response_model=list[ReadNoteSchema],
        summary="Get user notes",
        status_code=status.HTTP_200_OK,
    )
    router.add_api_route(
        path="/wikilink-suggestions",
        endpoint=get_wikilink_suggestions,
        methods=["GET"],
        response_model=list[WikilinkSuggestionSchema],
        summary="Search wikilink suggestions",
        status_code=status.HTTP_200_OK,
    )
    router.add_api_route(
        path="/search/by-title",
        endpoint=search_notes_by_title,
        methods=["GET"],
        response_model=list[ReadNoteSchema],
        summary="Search notes by title",
        status_code=status.HTTP_200_OK,
    )
    router.add_api_route(
        path="/creation-stats",
        endpoint=get_note_creation_stats,
        methods=["GET"],
        response_model=list[NoteCreationStatSchema],
        summary="Get note creation stats by date",
        status_code=status.HTTP_200_OK,
    )
    router.add_api_route(
        path="/new-title",
        endpoint=get_new_note_title,
        methods=["GET"],
        response_model=NewNoteTitleSchema,
        summary="Get next untitled note title",
        status_code=status.HTTP_200_OK,
    )
    router.add_api_route(
        path="",
        endpoint=create_note,
        methods=["POST"],
        response_model=ReadNoteSchema,
        summary="Create note",
        status_code=status.HTTP_201_CREATED,
    )
    router.add_api_route(
        path="/{note_id}",
        endpoint=delete_note,
        methods=["DELETE"],
        summary="Delete note",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    router.add_api_route(
        path="/{note_id}",
        endpoint=update_note,
        methods=["PATCH"],
        response_model=ReadNoteSchema,
        summary="Update note",
        status_code=status.HTTP_200_OK,
    )
    router.add_api_route(
        path="/export",
        endpoint=export_notes,
        methods=["GET"],
        summary="Export notes",
        status_code=status.HTTP_200_OK,
    )
    router.add_api_route(
        path="/import",
        endpoint=import_notes,
        methods=["POST"],
        summary="Import notes",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    return router
