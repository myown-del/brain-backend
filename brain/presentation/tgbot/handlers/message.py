from aiogram.types import Message
from dishka import AsyncContainer

from brain.application.interactors import (
    CreateDraftInteractor,
    GetUserInteractor,
)
from brain.application.interactors.drafts.dto import CreateDraft
from brain.application.interactors.users.exceptions import UserNotFoundException
from brain.infrastructure.telegram.attachment_upload import MessageAttachmentUploadController


async def handle_message(m: Message, dishka_container: AsyncContainer):
    create_draft_interactor = await dishka_container.get(CreateDraftInteractor)
    get_user_interactor = await dishka_container.get(GetUserInteractor)
    attachment_upload_controller = await dishka_container.get(MessageAttachmentUploadController)
    try:
        file_id = None
        if attachment_upload_controller.has_supported_attachment(m):
            file_id = await attachment_upload_controller.upload_attachment(m)

        user = await get_user_interactor.get_user_by_telegram_id(m.from_user.id)
        await create_draft_interactor.create_draft(
            CreateDraft(
                user_id=user.id,
                text=m.text or m.caption,
                file_id=file_id,
            )
        )
    except UserNotFoundException:
        await m.reply(f"Вы не авторизованы")
        return
    except Exception:
        await m.reply(f"Ошибка создания черновика")
        return

    await m.reply("Черновик сохранен")
