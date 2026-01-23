import pytest
from brain.domain.entities.user import User
from brain.infrastructure.db.repositories.hub import RepositoryHub


@pytest.mark.asyncio
async def test_users_repository_get_all(
    repo_hub: RepositoryHub,
    user: User,
):
    users_repository = repo_hub.users
    # Check that get_all returns the user created in fixture
    all_users = await users_repository.get_all()
    assert len(all_users) >= 1
    assert any(u.id == user.id for u in all_users)

    # Create another user and check
    new_user = User(
        id=user.id,  # Will be ignored/overwritten by factory/mapper usually, but let's assume valid user creation logic in repo text
        telegram_id=123456,
        username="test_user_2",
        first_name="Test",
        last_name="User",
    )
    # Since repository uses map_user_to_db which generates ID if not present or uses existing.
    # But wait, create method in repo:
    # db_model = map_user_to_db(entity) -> self._session.add(db_model)
    # Let's just use the repo to create another user

    # We need a fresh user with different content
    user2 = User(
        id=user.id,  # Logic needs uuid check, but let's rely on mapping
        telegram_id=999999,
        username="another_user",
        first_name="Another",
        last_name="One",
    )
    # Ideally should generate new ID
    from uuid import uuid4

    user2.id = uuid4()

    await users_repository.create(user2)

    all_users_after = await users_repository.get_all()
    assert len(all_users_after) == len(all_users) + 1
    assert any(u.id == user2.id for u in all_users_after)
