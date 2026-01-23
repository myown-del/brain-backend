from dishka import Provider, Scope, provide

from brain.application.abstractions.services.profile_picture_provider import (
    IProfilePictureProvider,
    ProfilePictureData,
)


class MockProfilePictureProvider(IProfilePictureProvider):
    async def get_profile_picture_content(
        self,
        telegram_id: int,
    ) -> ProfilePictureData | None:
        return None  # Return None by default for tests


class TestProfilePictureProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def get_provider(self) -> IProfilePictureProvider:
        return MockProfilePictureProvider()
