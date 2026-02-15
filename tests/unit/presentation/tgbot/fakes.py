from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass
class FakeUser:
    id: int
    username: Optional[str] = None
    first_name: str = ""
    last_name: Optional[str] = None
    is_bot: bool = False


@dataclass
class FakeMessage:
    from_user: FakeUser
    text: Optional[str] = None
    caption: Optional[str] = None
    photo: Optional[List[Any]] = None
    document: Optional[Any] = None
    video: Optional[Any] = None
    audio: Optional[Any] = None
    video_note: Optional[Any] = None
    voice: Optional[Any] = None
    bot: Optional[Any] = None
    replies: List[str] = field(default_factory=list)

    async def reply(self, text: str) -> None:
        self.replies.append(text)


@dataclass
class FakeCommand:
    args: Optional[str] = None


@dataclass
class FakeMessageEvent:
    from_user: Any


@dataclass
class FakeCallbackQueryEvent:
    from_user: Any


@dataclass
class FakeEvent:
    message: Optional[Any] = None
    callback_query: Optional[Any] = None


@dataclass
class FakeFromUserEvent:
    from_user: Any


class FakeContainer:
    def __init__(self, mapping: Dict[Any, Any]):
        self._mapping = mapping
        self.get_calls: List[Any] = []

    async def get(self, key: Any) -> Any:
        self.get_calls.append(key)
        return self._mapping[key]


class FakeDialogManager:
    def __init__(self):
        self.start_calls: List[Dict[str, Any]] = []

    async def start(self, **kwargs: Any) -> None:
        self.start_calls.append(kwargs)


class HandlerRecorder:
    def __init__(self, result: Any = None):
        self.calls: List[tuple[Any, Any]] = []
        self.result = result

    async def __call__(self, event: Any, data: Dict[str, Any]) -> Any:
        self.calls.append((event, data))
        return self.result


class FakeCreateNoteInteractor:
    def __init__(self, error: Exception | None = None):
        self.error = error
        self.calls: List[Any] = []

    async def create_note(self, payload: Any) -> None:
        self.calls.append(payload)
        if self.error:
            raise self.error


class FakeCreateDraftInteractor:
    def __init__(self, error: Exception | None = None):
        self.error = error
        self.calls: List[Any] = []

    async def create_draft(self, payload: Any) -> None:
        self.calls.append(payload)
        if self.error:
            raise self.error


class FakeGetUserInteractor:
    def __init__(self, user_id: Any | None = None, error: Exception | None = None):
        self.error = error
        self.calls: List[int] = []
        self.user = type("UserStub", (), {"id": user_id or uuid4()})()

    async def get_user_by_telegram_id(self, telegram_id: int) -> Any:
        self.calls.append(telegram_id)
        if self.error:
            raise self.error
        return self.user


class FakeUploadFileInteractor:
    def __init__(self, error: Exception | None = None):
        self.error = error
        self.calls: List[Dict[str, Any]] = []
        self.file_id = uuid4()

    async def upload_file(self, filename: str | None, content: bytes, content_type: str | None = None) -> Any:
        self.calls.append(
            {
                "filename": filename,
                "content": content,
                "content_type": content_type,
            }
        )
        if self.error:
            raise self.error
        return type("UploadedFileStub", (), {"id": self.file_id})()


class FakeAuthSessionInteractor:
    def __init__(self):
        self.calls: List[Dict[str, Any]] = []

    async def attach_user_to_session(self, **kwargs: Any) -> None:
        self.calls.append(kwargs)


class FakeUserInteractor:
    def __init__(self):
        self.calls: List[Any] = []

    async def create_or_update_user(self, payload: Any) -> None:
        self.calls.append(payload)


class FakeGetNotesInteractor:
    def __init__(self, notes: list[Any]):
        self.notes = notes
        self.calls: List[Dict[str, Any]] = []

    async def get_notes(self, **kwargs: Any) -> list[Any]:
        self.calls.append(kwargs)
        return self.notes


class FakeGetNoteInteractor:
    def __init__(self, note: Any):
        self.note = note
        self.calls: List[Any] = []

    async def get_note_by_id(self, note_id: Any) -> Any:
        self.calls.append(note_id)
        return self.note
