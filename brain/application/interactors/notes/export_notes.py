import io
import json
import zipfile
from dataclasses import asdict

from brain.application.abstractions.repositories.notes import INotesRepository
from brain.application.services.user_lookup import UserLookupService
from brain.domain.services import sanitize_filename


class ExportNotesInteractor:
    def __init__(
        self,
        user_lookup_service: UserLookupService,
        notes_repo: INotesRepository,
    ):
        self._user_lookup_service = user_lookup_service
        self._notes_repo = notes_repo

    async def export_notes(self, user_telegram_id: int) -> bytes:
        await self._user_lookup_service.get_user_by_telegram_id(user_telegram_id)
        notes = await self._notes_repo.get_by_user_telegram_id(user_telegram_id)

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for note in notes:
                note_dict = asdict(note)
                note_dict["id"] = str(note_dict["id"])
                note_dict["user_id"] = str(note_dict["user_id"])
                note_dict["represents_keyword_id"] = (
                    str(note_dict["represents_keyword_id"]) if note_dict["represents_keyword_id"] else None
                )
                if note_dict["created_at"]:
                    note_dict["created_at"] = note_dict["created_at"].isoformat()
                if note_dict["updated_at"]:
                    note_dict["updated_at"] = note_dict["updated_at"].isoformat()

                filename = f"{sanitize_filename(note.title)}.json"
                zip_file.writestr(filename, json.dumps(note_dict, indent=2))

        return zip_buffer.getvalue()
