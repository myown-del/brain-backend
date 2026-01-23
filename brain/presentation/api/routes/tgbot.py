from aiogram import Dispatcher, Bot
from aiogram.types import Update
from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter
from starlette.requests import Request

from brain.config.models import APIConfig


@inject
async def handle_webhook(
        request: Request,
        bot: FromDishka[Bot],
        dp: FromDishka[Dispatcher],
):
    data = await request.json()
    update = Update(**data)
    await dp.feed_webhook_update(bot=bot, update=update)


def get_router(config: APIConfig) -> APIRouter:
    router = APIRouter()
    router.add_api_route(
        path='/tg-bot/webhook',
        endpoint=handle_webhook,
        methods=["POST"],
    )
    return router
