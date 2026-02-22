from brain.infrastructure.db.repositories.hub import RepositoryHub
from brain.infrastructure.db.uow import SqlAlchemyUnitOfWork


async def commit_repo_hub(repo_hub: RepositoryHub) -> None:
    async with SqlAlchemyUnitOfWork(repo_hub.users._session) as uow:  # type: ignore[attr-defined]
        await uow.commit()
