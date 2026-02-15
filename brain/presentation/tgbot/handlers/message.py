from aiogram.types import Message
from dishka import AsyncContainer

from brain.application.interactors import CreateDraftInteractor, GetUserInteractor
from brain.application.interactors.drafts.dto import CreateDraft
from brain.application.interactors.users.exceptions import UserNotFoundException


async def handle_message(m: Message, dishka_container: AsyncContainer):
    create_draft_interactor = await dishka_container.get(CreateDraftInteractor)
    get_user_interactor = await dishka_container.get(GetUserInteractor)
    try:
        user = await get_user_interactor.get_user_by_telegram_id(m.from_user.id)
        await create_draft_interactor.create_draft(
            CreateDraft(
                user_id=user.id,
                text=m.text,
            )
        )
    except UserNotFoundException:
        await m.reply(f"Вы не авторизованы")
        return
    except Exception:
        await m.reply(f"Ошибка создания черновика")
        return

    await m.reply("Черновик сохранен")
