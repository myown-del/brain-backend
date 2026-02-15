from aiogram import Bot
from dishka import Provider, Scope, provide

from brain.application.abstractions.services.profile_picture_provider import (
    IProfilePictureProvider,
)
from brain.application.interactors import UploadFileInteractor
from brain.infrastructure.telegram.attachment_upload import MessageAttachmentUploadController
from brain.infrastructure.telegram.profile_picture_provider import (
    TelegramProfilePictureProvider,
)


class TelegramInfrastructureProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def get_message_attachment_upload_controller(
        self,
        upload_file_interactor: UploadFileInteractor,
    ) -> MessageAttachmentUploadController:
        return MessageAttachmentUploadController(upload_file_interactor=upload_file_interactor)

    @provide(scope=Scope.REQUEST, provides=IProfilePictureProvider)
    async def get_telegram_profile_picture_provider(self, bot: Bot) -> TelegramProfilePictureProvider:
        return TelegramProfilePictureProvider(bot=bot)
