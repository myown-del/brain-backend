import asyncio
import logging
from pathlib import Path

from alembic import command
from alembic.config import Config as AlembicConfig
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
PROJECT_ROOT = Path(__file__).resolve().parents[4]
MIGRATIONS_PATH = PROJECT_ROOT / "brain" / "infrastructure" / "migrations"
ALEMBIC_CONFIG_PATH = PROJECT_ROOT / "alembic.ini"


def run_database_migrations(config: Config) -> None:
    alembic_cfg = AlembicConfig(str(ALEMBIC_CONFIG_PATH))
    alembic_cfg.set_main_option("script_location", str(MIGRATIONS_PATH))
    alembic_cfg.set_main_option("sqlalchemy.url", config.db.uri)
    alembic_cfg.attributes["configure_logger"] = False
    command.upgrade(alembic_cfg, "head")
    logger.info("Database migrations applied")


async def setup_webhook(container: AsyncContainer, config: APIConfig):
    webhook_url = f"{config.external_host}/api/tg-bot/webhook"

    bot = await container.get(Bot)
    await bot.set_webhook(url=webhook_url)
    logger.info(f"Binded bot webhooks to url: {webhook_url}")


def prepare_config() -> Config:
    config = load_config(config_class=Config, env_file_path=".env")
    setup_logging(config.logging_level)
    run_database_migrations(config)
    return config


async def main(config: Config):
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

    await setup_webhook(container, config.api)
    logger.info("Tasks setup complete")


if __name__ == "__main__":
    config = prepare_config()
    asyncio.run(main(config))
