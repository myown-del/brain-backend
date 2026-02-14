from brain.domain.entities.tg_bot_auth import TelegramBotAuthSession
from brain.infrastructure.db.mappers import normalize_datetime
from brain.infrastructure.db.models.tg_bot_auth import TelegramBotAuthSessionDB


def map_telegram_bot_auth_session_to_dm(
    session: TelegramBotAuthSessionDB,
) -> TelegramBotAuthSession:
    return TelegramBotAuthSession(
        id=session.id,
        telegram_id=session.user_id,
        jwt_token_id=session.jwt_token_id,
        created_at=normalize_datetime(session.created_at),
    )


def map_telegram_bot_auth_session_to_db(
    session: TelegramBotAuthSession,
) -> TelegramBotAuthSessionDB:
    return TelegramBotAuthSessionDB(
        id=session.id,
        user_id=session.telegram_id,
        jwt_token_id=session.jwt_token_id,
        created_at=normalize_datetime(session.created_at),
    )

