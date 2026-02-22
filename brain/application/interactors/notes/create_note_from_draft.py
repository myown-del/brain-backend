from uuid import UUID

from brain.application.abstractions.repositories.drafts import IDraftsRepository
from brain.application.abstractions.uow import UnitOfWorkFactory
from brain.application.interactors.drafts.exceptions import DraftNotFoundException
from brain.application.interactors.notes.dto import CreateNote, CreateNoteFromDraft
from brain.application.services.note_crud import NoteCreationService
from brain.application.services.user_lookup import UserLookupService
from brain.config.models import S3Config
from brain.domain.services.media import build_public_file_url


class DraftForbiddenException(Exception):
    pass


class CreateNoteFromDraftInteractor:
    def __init__(
        self,
        user_lookup_service: UserLookupService,
        drafts_repo: IDraftsRepository,
        note_creation_service: NoteCreationService,
        s3_config: S3Config,
        uow_factory: UnitOfWorkFactory,
    ):
        self._user_lookup_service = user_lookup_service
        self._drafts_repo = drafts_repo
        self._note_creation_service = note_creation_service
        self._s3_config = s3_config
        self._uow_factory = uow_factory

    def _build_note_text(self, draft_text: str | None, filename: str, file_path: str) -> str:
        file_url = build_public_file_url(
            external_host=self._s3_config.external_host,
            file_path=file_path,
        )
        markdown_image = f"![{filename}]({file_url})"
        if not draft_text:
            return markdown_image
        return f"{draft_text}\n\n{markdown_image}"

    async def create_note_from_draft(self, note_data: CreateNoteFromDraft) -> UUID:
        async with self._uow_factory() as uow:
            user = await self._user_lookup_service.get_user_by_telegram_id(note_data.by_user_telegram_id)
            draft = await self._drafts_repo.get_by_id(note_data.draft_id)
            if draft is None:
                raise DraftNotFoundException()
            if draft.user_id != user.id:
                raise DraftForbiddenException()

            note_text = draft.text
            if draft.file and draft.file.name and draft.file.path:
                note_text = self._build_note_text(
                    draft_text=draft.text,
                    filename=draft.file.name,
                    file_path=draft.file.path,
                )

            await self._drafts_repo.delete_by_id(draft.id)
            note_id = await self._note_creation_service.create_note(
                CreateNote(
                    by_user_telegram_id=note_data.by_user_telegram_id,
                    title=note_data.title,
                    text=note_text,
                )
            )
            await uow.commit()
            return note_id
