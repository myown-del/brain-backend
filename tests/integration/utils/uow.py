from brain.infrastructure.db.repositories.hub import RepositoryHub


async def commit_repo_hub(repo_hub: RepositoryHub) -> None:
    await repo_hub.users._session.commit()  # type: ignore[attr-defined]
