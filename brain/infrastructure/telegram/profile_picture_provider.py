from io import BytesIO

from aiogram import Bot

from brain.application.abstractions.services.profile_picture_provider import (
    IProfilePictureProvider,
    ProfilePictureData,
)
from brain.domain.services.media import guess_image_content_type


class TelegramProfilePictureProvider(IProfilePictureProvider):
    def __init__(self, bot: Bot):
        self._bot = bot

    async def get_profile_picture_content(self, telegram_id: int) -> tuple[bytes, str] | None:
        photos = await self._bot.get_user_profile_photos(user_id=telegram_id, limit=1)
        if not photos.photos:
            return None

        photo = photos.photos[0][-1]
        file = await self._bot.get_file(photo.file_id)
        if not file.file_path:
            return None

        buffer = BytesIO()
        await self._bot.download_file(file.file_path, destination=buffer)
        content = buffer.getvalue()
        if not content:
            return None

        content_type = guess_image_content_type(file.file_path) or "image/jpeg"
        return ProfilePictureData(content=content, content_type=content_type)
