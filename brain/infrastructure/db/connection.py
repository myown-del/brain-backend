from sqlalchemy import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine, AsyncEngine

from brain.application.abstractions.config.models import IDatabaseConfig


def create_engine(config: IDatabaseConfig) -> AsyncEngine:
    return create_async_engine(
        url=make_url(config.uri),
        pool_pre_ping=True,
        pool_recycle=1800,
    )


def create_session_maker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    pool: async_sessionmaker[AsyncSession] = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        autoflush=False,
    )
    return pool
