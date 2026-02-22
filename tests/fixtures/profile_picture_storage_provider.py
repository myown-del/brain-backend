from dishka import Provider, Scope, provide

from brain.application.abstractions.storage.files import IFileStorage
from brain.application.abstractions.storage.user_profile_pictures import IProfilePictureStorage


class FakeProfilePictureStorage(IProfilePictureStorage):
    def __init__(self, base_url: str = "https://avatars.test"):
        self._base_url = base_url

    def upload(
        self,
        content: bytes,
        object_name: str,
        content_type: str | None = None,
    ) -> str:
        return f"{self._base_url}/{object_name}"


class FakeFileStorage(IFileStorage):
    def __init__(self, base_url: str = "https://files.test"):
        self._base_url = base_url

    def upload(
        self,
        content: bytes,
        object_name: str,
        content_type: str | None = None,
    ) -> str:
        return f"{self._base_url}/{object_name}"


class TestProfilePictureStorageProvider(Provider):
    scope = Scope.APP

    @provide(provides=IProfilePictureStorage)
    def get_profile_picture_storage(self) -> IProfilePictureStorage:
        return FakeProfilePictureStorage()

    @provide(provides=IFileStorage)
    def get_file_storage(self) -> IFileStorage:
        return FakeFileStorage()
