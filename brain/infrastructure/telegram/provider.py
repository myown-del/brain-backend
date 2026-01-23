from aiogram import Bot
from dishka import Provider, Scope, provide

from brain.application.abstractions.services.profile_picture_provider import (
    IProfilePictureProvider,
)
from brain.infrastructure.telegram.profile_picture_provider import (
    TelegramProfilePictureProvider,
)


class TelegramInfrastructureProvider(Provider):
    @provide(scope=Scope.REQUEST, provides=IProfilePictureProvider)
    async def get_telegram_profile_picture_provider(self, bot: Bot) -> TelegramProfilePictureProvider:
        return TelegramProfilePictureProvider(bot=bot)
