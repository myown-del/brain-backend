import pytest
from dishka import AsyncContainer

from brain.application.interactors import UploadUserProfilePictureInteractor
from brain.domain.entities.user import User
from brain.infrastructure.db.repositories.hub import RepositoryHub


@pytest.mark.asyncio
async def test_upload_user_profile_picture_creates_record(
    dishka_request: AsyncContainer,
    repo_hub: RepositoryHub,
    user: User,
):
    # setup: prepare interactor and content
    interactor = await dishka_request.get(UploadUserProfilePictureInteractor)
    content = b"avatar-bytes"

    # action: upload profile picture for user
    profile_picture = await interactor.upload_profile_picture(
        telegram_id=user.telegram_id,
        image_content=content,
        content_type="image/jpeg",
    )

    # check: profile picture stored in database
    stored = await repo_hub.s3_files.get_by_user_id(user.id)
    assert stored is not None
    assert stored.id == profile_picture.id
    assert f"/avatars/{user.id}/" in f"/{stored.path}"
    assert stored.name.endswith(".jpg")
    assert stored.content_type == "image/jpeg"
    updated_user = await repo_hub.users.get_by_id(user.id)
    assert updated_user.profile_picture_file_id == profile_picture.id


@pytest.mark.asyncio
async def test_upload_user_profile_picture_updates_existing_record(
    dishka_request: AsyncContainer,
    repo_hub: RepositoryHub,
    user: User,
):
    # setup: prepare interactor and initial profile picture
    interactor = await dishka_request.get(UploadUserProfilePictureInteractor)
    first_profile_picture = await interactor.upload_profile_picture(
        telegram_id=user.telegram_id,
        image_content=b"avatar-bytes",
        content_type="image/jpeg",
    )

    # action: upload new profile picture for same user
    second_profile_picture = await interactor.upload_profile_picture(
        telegram_id=user.telegram_id,
        image_content=b"avatar-bytes-2",
        content_type="image/png",
    )

    # check: profile picture updated in database
    stored = await repo_hub.s3_files.get_by_user_id(user.id)
    assert stored is not None
    assert stored.id == first_profile_picture.id
    assert stored.name == second_profile_picture.name
    assert stored.path == second_profile_picture.path
    assert stored.content_type == "image/png"
    updated_user = await repo_hub.users.get_by_id(user.id)
    assert updated_user.profile_picture_file_id == first_profile_picture.id
