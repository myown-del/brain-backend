import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from brain.application.interactors.users.update_all_profile_pictures import (
    UpdateAllUsersProfilePicturesInteractor,
)
from brain.domain.entities.user import User
from brain.infrastructure.db.repositories.users import UsersRepository
from brain.application.abstractions.repositories.users import IUsersRepository
from tests.fixtures.profile_picture_provider import MockProfilePictureProvider

from brain.application.abstractions.services.profile_picture_provider import ProfilePictureData

from dishka import AsyncContainer


@pytest.mark.asyncio
async def test_update_all_profile_pictures(
    dishka_request: AsyncContainer,
    user: User,
):
    update_all_users_profile_pictures_interactor = await dishka_request.get(UpdateAllUsersProfilePicturesInteractor)
    users_repository = await dishka_request.get(IUsersRepository)

    # Setup mock provider to return some dummy content
    
    with patch.object(
        MockProfilePictureProvider, 
        'get_profile_picture_content', 
        new_callable=AsyncMock,
    ) as mock_get:
        mock_get.return_value = ProfilePictureData(content=b"fake_image_content", content_type="image/png")
        
        # Execute the interactor
        await update_all_users_profile_pictures_interactor.execute()
        
        # Verify provider was called for our user
        mock_get.assert_any_call(user.telegram_id)
        
        # Verify user was updated
        updated_user = await users_repository.get_by_id(user.id)
        assert updated_user.profile_picture_file_id is not None
        
        # We could also verify S3 but checking the user entity update is a strong enough signal for this integration level
