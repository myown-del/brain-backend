import asyncio
import logging

from dishka import make_async_container, AsyncContainer
from aiogram import Bot

from brain.config.provider import ConfigProvider, DatabaseConfigProvider
from brain.config.models import APIConfig, Config
from brain.config.parser import load_config
from brain.infrastructure.jwt.provider import JwtProvider
from brain.infrastructure.s3.provider import S3Provider
from brain.main.log import setup_logging
from brain.presentation.tgbot.provider import DispatcherProvider, BotProvider
from brain.infrastructure.db.provider import DatabaseProvider
from brain.infrastructure.graph.provider import Neo4jProvider
from brain.infrastructure.telegram.provider import TelegramInfrastructureProvider
from brain.application.interactors.factory import InteractorProvider

logger = logging.getLogger(__name__)


async def setup_tasks(container: AsyncContainer, config: APIConfig):
    webhook_url = f"{config.external_host}/api/tg-bot/webhook"

    bot = await container.get(Bot)
    await bot.set_webhook(url=webhook_url)
    logger.info(f"Binded bot webhooks to url: {webhook_url}")


async def main():
    config = load_config(config_class=Config, env_file_path=".env")
    setup_logging(config.logging_level)
    container = make_async_container(
        ConfigProvider(),
        BotProvider(),
        DatabaseConfigProvider(),
        DatabaseProvider(),
        Neo4jProvider(),
        S3Provider(),
        InteractorProvider(),
        TelegramInfrastructureProvider(),
        JwtProvider(),
        DispatcherProvider(),
        context={Config: config},
    )

    await setup_tasks(container, config.api)
    logger.info("Tasks setup complete")


if __name__ == "__main__":
    asyncio.run(main())
