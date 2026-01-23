from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dishka import Provider, Scope, provide

from brain.config.models import BotConfig


class BotProvider(Provider):
    scope = Scope.APP

    @provide
    async def create_bot(self, bot_config: BotConfig) -> Bot:
        bot = Bot(
            token=bot_config.token,
            default=DefaultBotProperties(
                parse_mode=ParseMode.HTML, allow_sending_without_reply=True,
            ),
        )
        return bot
