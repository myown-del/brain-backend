import sys

from dishka import make_async_container
from dishka.integrations.taskiq import setup_dishka
from taskiq import TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource
from taskiq_redis import RedisStreamBroker

from brain.application.interactors.factory import InteractorProvider
from brain.config.models import Config
from brain.config.parser import load_config
from brain.config.provider import ConfigProvider, DatabaseConfigProvider
from brain.infrastructure.db.provider import DatabaseProvider
from brain.infrastructure.graph.provider import Neo4jProvider
from brain.infrastructure.jwt.provider import JwtProvider
from brain.infrastructure.s3.provider import S3Provider
from brain.infrastructure.telegram.provider import TelegramInfrastructureProvider

config = load_config(
    config_class=Config,
    env_file_path=".env",
)

broker = RedisStreamBroker(url=config.redis.uri)
scheduler = TaskiqScheduler(
    broker=broker,
    sources=[LabelScheduleSource(broker)],
)
container = None


def setup_broker() -> None:
    global container
    if container is not None:
        return

    # Local imports to avoid circular dependency with tgbot tasks -> broker.
    from brain.presentation.tgbot.bot_provider import BotProvider
    from brain.presentation.tgbot.provider import DispatcherProvider

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
    setup_dishka(container=container, broker=broker)


if "pytest" not in sys.modules:
    setup_broker()
