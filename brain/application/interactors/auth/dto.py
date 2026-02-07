from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from brain.domain.entities.jwt import FullJwtToken
from brain.domain.entities.tg_bot_auth import TelegramBotAuthSession


@dataclass
class JwtTokenCreationPayload:
    user_id: UUID


@dataclass
class DecodedJwtTokenPayload:
    user_id: UUID
    exp: datetime


@dataclass
class TelegramBotAuthSessionTokens:
    session: TelegramBotAuthSession
    tokens: FullJwtToken | None


@dataclass
class CreatedApiKey:
    id: UUID
    name: str
    key: str
    created_at: datetime
