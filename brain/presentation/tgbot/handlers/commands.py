from aiogram.filters import CommandObject
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode
from dishka import AsyncContainer

from brain.application.interactors.auth.session_interactor import (
    TelegramBotAuthSessionInteractor,
)

from brain.presentation.tgbot.states import MainMenu


async def handle_start_cmd(
    message: Message,
    command: CommandObject,
    dialog_manager: DialogManager,
    dishka_container: AsyncContainer,
):
    session_id = None
    if command.args and command.args.startswith("tgauth_"):
        session_id = command.args.removeprefix("tgauth_").strip()

    if session_id and message.from_user:
        interactor = await dishka_container.get(TelegramBotAuthSessionInteractor)
        await interactor.attach_user_to_session(
            session_id=session_id,
            telegram_id=message.from_user.id,
        )

    if message.from_user and not message.from_user.is_bot:
        from brain.presentation.tgbot.tasks import upload_user_profile_picture_task

        await upload_user_profile_picture_task.kiq(telegram_id=message.from_user.id)

    await dialog_manager.start(state=MainMenu.main_menu, mode=StartMode.RESET_STACK)
