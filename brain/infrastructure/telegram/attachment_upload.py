from __future__ import annotations

from abc import ABC, abstractmethod
from io import BytesIO
from mimetypes import guess_type
from typing import Sequence
from uuid import UUID

from aiogram.types import Message

from brain.application.interactors import UploadFileInteractor
from brain.domain.services.message_attachment_uploader import IMessageAttachmentUploader
from brain.domain.services.media import guess_image_content_type


class BaseMessageAttachmentUploader(IMessageAttachmentUploader, ABC):
    @abstractmethod
    def can_handle(self, message: Message) -> bool:
        raise NotImplementedError

    @abstractmethod
    def _extract_file_id(self, message: Message) -> str | None:
        raise NotImplementedError

    @abstractmethod
    def _resolve_filename(self, message: Message, file_path: str) -> str | None:
        raise NotImplementedError

    @abstractmethod
    def _resolve_content_type(self, message: Message, file_path: str) -> str | None:
        raise NotImplementedError

    async def upload(
        self,
        message: Message,
        upload_file_interactor: UploadFileInteractor,
    ) -> UUID | None:
        if message.bot is None:
            return None

        telegram_file_id = self._extract_file_id(message)
        if not telegram_file_id:
            return None

        file = await message.bot.get_file(telegram_file_id)
        if not file.file_path:
            return None

        buffer = BytesIO()
        await message.bot.download_file(file.file_path, destination=buffer)
        content = buffer.getvalue()
        if not content:
            return None

        uploaded_file = await upload_file_interactor.upload_file(
            filename=self._resolve_filename(message, file.file_path),
            content=content,
            content_type=self._resolve_content_type(message, file.file_path),
        )
        return uploaded_file.id


class PhotoMessageAttachmentUploader(BaseMessageAttachmentUploader):
    def can_handle(self, message: Message) -> bool:
        return bool(message.photo)

    def _extract_file_id(self, message: Message) -> str | None:
        if not message.photo:
            return None
        return message.photo[-1].file_id

    def _resolve_filename(self, message: Message, file_path: str) -> str | None:
        return file_path

    def _resolve_content_type(self, message: Message, file_path: str) -> str | None:
        return guess_image_content_type(file_path)


class DocumentMessageAttachmentUploader(BaseMessageAttachmentUploader):
    def can_handle(self, message: Message) -> bool:
        return message.document is not None

    def _extract_file_id(self, message: Message) -> str | None:
        if message.document is None:
            return None
        return message.document.file_id

    def _resolve_filename(self, message: Message, file_path: str) -> str | None:
        if message.document is None:
            return file_path
        return message.document.file_name or file_path

    def _resolve_content_type(self, message: Message, file_path: str) -> str | None:
        if message.document is None:
            return None
        return message.document.mime_type


class VideoMessageAttachmentUploader(BaseMessageAttachmentUploader):
    def can_handle(self, message: Message) -> bool:
        return message.video is not None

    def _extract_file_id(self, message: Message) -> str | None:
        if message.video is None:
            return None
        return message.video.file_id

    def _resolve_filename(self, message: Message, file_path: str) -> str | None:
        if message.video is None:
            return file_path
        return message.video.file_name or file_path

    def _resolve_content_type(self, message: Message, file_path: str) -> str | None:
        if message.video is None:
            return guess_type(file_path)[0]
        return message.video.mime_type or guess_type(file_path)[0]


class AudioMessageAttachmentUploader(BaseMessageAttachmentUploader):
    def can_handle(self, message: Message) -> bool:
        return message.audio is not None

    def _extract_file_id(self, message: Message) -> str | None:
        if message.audio is None:
            return None
        return message.audio.file_id

    def _resolve_filename(self, message: Message, file_path: str) -> str | None:
        if message.audio is None:
            return file_path
        return message.audio.file_name or file_path

    def _resolve_content_type(self, message: Message, file_path: str) -> str | None:
        if message.audio is None:
            return guess_type(file_path)[0]
        return message.audio.mime_type or guess_type(file_path)[0]


class VideoNoteMessageAttachmentUploader(BaseMessageAttachmentUploader):
    def can_handle(self, message: Message) -> bool:
        return message.video_note is not None

    def _extract_file_id(self, message: Message) -> str | None:
        if message.video_note is None:
            return None
        return message.video_note.file_id

    def _resolve_filename(self, message: Message, file_path: str) -> str | None:
        return file_path

    def _resolve_content_type(self, message: Message, file_path: str) -> str | None:
        return "video/mp4"


class VoiceMessageAttachmentUploader(BaseMessageAttachmentUploader):
    def can_handle(self, message: Message) -> bool:
        return message.voice is not None

    def _extract_file_id(self, message: Message) -> str | None:
        if message.voice is None:
            return None
        return message.voice.file_id

    def _resolve_filename(self, message: Message, file_path: str) -> str | None:
        return file_path

    def _resolve_content_type(self, message: Message, file_path: str) -> str | None:
        if message.voice is None:
            return "audio/ogg"
        return message.voice.mime_type or "audio/ogg"


class MessageAttachmentUploadController:
    def __init__(
        self,
        upload_file_interactor: UploadFileInteractor,
        uploaders: Sequence[BaseMessageAttachmentUploader] | None = None,
    ):
        self._upload_file_interactor = upload_file_interactor
        self._uploaders = list(
            uploaders
            or (
                PhotoMessageAttachmentUploader(),
                DocumentMessageAttachmentUploader(),
                VideoMessageAttachmentUploader(),
                AudioMessageAttachmentUploader(),
                VideoNoteMessageAttachmentUploader(),
                VoiceMessageAttachmentUploader(),
            )
        )

    def has_supported_attachment(self, message: Message) -> bool:
        return any(uploader.can_handle(message) for uploader in self._uploaders)

    async def upload_attachment(
        self,
        message: Message,
    ) -> UUID | None:
        for uploader in self._uploaders:
            if uploader.can_handle(message):
                return await uploader.upload(message, self._upload_file_interactor)
        return None
