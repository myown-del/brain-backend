from dataclasses import dataclass
from typing import Protocol


@dataclass
class ProfilePictureData:
    content: bytes
    content_type: str


class IProfilePictureProvider(Protocol):
    async def get_profile_picture_content(self, telegram_id: int) -> ProfilePictureData | None:
        """
        Get user profile picture content and content type.
        Returns:
            ProfilePictureData | None: Object containing content and content_type or None if no photo found
        """
        raise NotImplementedError
