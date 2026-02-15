from types import SimpleNamespace
from uuid import uuid4

import pytest
from aiogram_dialog import StartMode

from brain.application.interactors import (
    CreateDraftInteractor,
    GetUserInteractor,
)
from brain.application.interactors.auth.session_interactor import (
    TelegramBotAuthSessionInteractor,
)
from brain.application.interactors.drafts.dto import CreateDraft
from brain.application.interactors.users.exceptions import UserNotFoundException
from brain.infrastructure.telegram.attachment_upload import MessageAttachmentUploadController
from brain.presentation.tgbot.handlers.commands import handle_start_cmd
from brain.presentation.tgbot.handlers.message import handle_message
from brain.presentation.tgbot.states import MainMenu
from tests.unit.presentation.tgbot.fakes import (
    FakeAuthSessionInteractor,
    FakeCommand,
    FakeContainer,
    FakeCreateDraftInteractor,
    FakeDialogManager,
    FakeGetUserInteractor,
    FakeMessage,
    FakeUploadFileInteractor,
    FakeUser,
)


class EnqueueRecorder:
    def __init__(self):
        self.calls: list[int] = []

    async def __call__(self, telegram_id: int) -> None:
        self.calls.append(telegram_id)


class FakeBot:
    def __init__(self, file_path: str, content: bytes):
        self.file_path = file_path
        self.content = content
        self.get_file_calls: list[str] = []
        self.download_file_calls: list[str] = []

    async def get_file(self, file_id: str) -> SimpleNamespace:
        self.get_file_calls.append(file_id)
        return SimpleNamespace(file_path=self.file_path)

    async def download_file(self, file_path: str, destination) -> None:
        self.download_file_calls.append(file_path)
        destination.write(self.content)


@pytest.mark.asyncio
async def test_handle_start_cmd_attaches_user_when_session(monkeypatch: pytest.MonkeyPatch):
    # setup: command with session id and user
    message = FakeMessage(from_user=FakeUser(id=111))
    command = FakeCommand(args="tgauth_abc")
    interactor = FakeAuthSessionInteractor()
    container = FakeContainer({TelegramBotAuthSessionInteractor: interactor})
    dialog_manager = FakeDialogManager()
    enqueue_recorder = EnqueueRecorder()
    monkeypatch.setattr(
        "brain.presentation.tgbot.tasks.upload_user_profile_picture_task.kiq",
        enqueue_recorder,
    )

    # action: handle start command
    await handle_start_cmd(message, command, dialog_manager, container)

    # check: user attached and dialog started
    assert interactor.calls == [{"session_id": "abc", "telegram_id": 111}]
    assert enqueue_recorder.calls == [111]
    assert dialog_manager.start_calls == [
        {"state": MainMenu.main_menu, "mode": StartMode.RESET_STACK},
    ]


@pytest.mark.asyncio
async def test_handle_start_cmd_skips_attach_without_session(monkeypatch: pytest.MonkeyPatch):
    # setup: command without session id
    message = FakeMessage(from_user=FakeUser(id=111))
    command = FakeCommand(args=None)
    container = FakeContainer({})
    dialog_manager = FakeDialogManager()
    enqueue_recorder = EnqueueRecorder()
    monkeypatch.setattr(
        "brain.presentation.tgbot.tasks.upload_user_profile_picture_task.kiq",
        enqueue_recorder,
    )

    # action: handle start command
    await handle_start_cmd(message, command, dialog_manager, container)

    # check: no interactor lookup and dialog started
    assert container.get_calls == []
    assert enqueue_recorder.calls == [111]
    assert dialog_manager.start_calls == [
        {"state": MainMenu.main_menu, "mode": StartMode.RESET_STACK},
    ]


@pytest.mark.asyncio
async def test_handle_start_cmd_skips_profile_picture_for_bot_user(monkeypatch: pytest.MonkeyPatch):
    # setup: bot user
    message = FakeMessage(from_user=FakeUser(id=222, is_bot=True))
    command = FakeCommand(args=None)
    container = FakeContainer({})
    dialog_manager = FakeDialogManager()
    enqueue_recorder = EnqueueRecorder()
    monkeypatch.setattr(
        "brain.presentation.tgbot.tasks.upload_user_profile_picture_task.kiq",
        enqueue_recorder,
    )

    # action: handle start command
    await handle_start_cmd(message, command, dialog_manager, container)

    # check: enqueue is skipped for bot users
    assert enqueue_recorder.calls == []
    assert dialog_manager.start_calls == [
        {"state": MainMenu.main_menu, "mode": StartMode.RESET_STACK},
    ]


@pytest.mark.asyncio
async def test_handle_message_creates_text_draft():
    # setup: message and draft interactors
    message = FakeMessage(from_user=FakeUser(id=55), text="hello")
    create_draft = FakeCreateDraftInteractor()
    get_user = FakeGetUserInteractor()
    upload_file = FakeUploadFileInteractor()
    attachment_upload_controller = MessageAttachmentUploadController(upload_file_interactor=upload_file)
    container = FakeContainer(
        {
            CreateDraftInteractor: create_draft,
            GetUserInteractor: get_user,
            MessageAttachmentUploadController: attachment_upload_controller,
        }
    )

    # action: handle incoming message
    await handle_message(message, container)

    # check: draft created and reply sent
    assert create_draft.calls == [
        CreateDraft(user_id=get_user.user.id, text="hello", file_id=None),
    ]
    assert message.replies == ["Черновик сохранен"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("message_kwargs", "telegram_file_id", "telegram_file_path", "expected_filename", "expected_content_type"),
    [
        (
            {"photo": [SimpleNamespace(file_id="photo-file-id")]},
            "photo-file-id",
            "photos/file.jpg",
            "photos/file.jpg",
            "image/jpeg",
        ),
        (
            {"document": SimpleNamespace(file_id="doc-file-id", file_name="report.pdf", mime_type="application/pdf")},
            "doc-file-id",
            "docs/file.pdf",
            "report.pdf",
            "application/pdf",
        ),
        (
            {"video": SimpleNamespace(file_id="video-file-id", file_name="clip.mp4", mime_type="video/mp4")},
            "video-file-id",
            "video/clip.mp4",
            "clip.mp4",
            "video/mp4",
        ),
        (
            {"audio": SimpleNamespace(file_id="audio-file-id", file_name="song.mp3", mime_type="audio/mpeg")},
            "audio-file-id",
            "audio/song.mp3",
            "song.mp3",
            "audio/mpeg",
        ),
        (
            {"video_note": SimpleNamespace(file_id="video-note-file-id")},
            "video-note-file-id",
            "video-note/note.mp4",
            "video-note/note.mp4",
            "video/mp4",
        ),
        (
            {"voice": SimpleNamespace(file_id="voice-file-id", mime_type="audio/ogg")},
            "voice-file-id",
            "voice/note.ogg",
            "voice/note.ogg",
            "audio/ogg",
        ),
    ],
)
async def test_handle_message_uploads_supported_attachments_and_attaches_file_to_draft(
    message_kwargs,
    telegram_file_id,
    telegram_file_path,
    expected_filename,
    expected_content_type,
):
    # setup: message with supported attachment
    bot = FakeBot(file_path=telegram_file_path, content=b"file-bytes")
    message = FakeMessage(
        from_user=FakeUser(id=55),
        caption="with attachment",
        bot=bot,
        **message_kwargs,
    )
    create_draft = FakeCreateDraftInteractor()
    get_user = FakeGetUserInteractor()
    upload_file = FakeUploadFileInteractor()
    attachment_upload_controller = MessageAttachmentUploadController(upload_file_interactor=upload_file)
    container = FakeContainer(
        {
            CreateDraftInteractor: create_draft,
            GetUserInteractor: get_user,
            MessageAttachmentUploadController: attachment_upload_controller,
        }
    )

    # action
    await handle_message(message, container)

    # check
    assert upload_file.calls == [
        {
            "filename": expected_filename,
            "content": b"file-bytes",
            "content_type": expected_content_type,
        }
    ]
    assert create_draft.calls == [
        CreateDraft(user_id=get_user.user.id, text="with attachment", file_id=upload_file.file_id),
    ]
    assert bot.get_file_calls == [telegram_file_id]
    assert bot.download_file_calls == [telegram_file_path]


@pytest.mark.asyncio
async def test_handle_message_replies_on_user_not_found():
    # setup: user lookup raises user-not-found
    message = FakeMessage(from_user=FakeUser(id=55), text="hello")
    create_draft = FakeCreateDraftInteractor()
    get_user = FakeGetUserInteractor(error=UserNotFoundException())
    upload_file = FakeUploadFileInteractor()
    attachment_upload_controller = MessageAttachmentUploadController(upload_file_interactor=upload_file)
    container = FakeContainer(
        {
            CreateDraftInteractor: create_draft,
            GetUserInteractor: get_user,
            MessageAttachmentUploadController: attachment_upload_controller,
        }
    )

    # action: handle incoming message
    await handle_message(message, container)

    # check
    assert create_draft.calls == []
    assert message.replies == ["Вы не авторизованы"]


@pytest.mark.asyncio
async def test_handle_message_replies_on_generic_error():
    # setup: draft creation raises generic error
    message = FakeMessage(from_user=FakeUser(id=55), text="hello")
    create_draft = FakeCreateDraftInteractor(error=RuntimeError("boom"))
    get_user = FakeGetUserInteractor(user_id=uuid4())
    upload_file = FakeUploadFileInteractor()
    attachment_upload_controller = MessageAttachmentUploadController(upload_file_interactor=upload_file)
    container = FakeContainer(
        {
            CreateDraftInteractor: create_draft,
            GetUserInteractor: get_user,
            MessageAttachmentUploadController: attachment_upload_controller,
        }
    )

    # action: handle incoming message
    await handle_message(message, container)

    # check
    assert message.replies == ["Ошибка создания черновика"]
