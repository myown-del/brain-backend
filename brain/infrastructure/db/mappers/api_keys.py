from brain.domain.entities.api_key import ApiKey
from brain.infrastructure.db.models.api_key import ApiKeyDB


def map_api_key_to_dm(api_key: ApiKeyDB) -> ApiKey:
    return ApiKey(
        id=api_key.id,
        user_id=api_key.user_id,
        name=api_key.name,
        key_hash=api_key.key_hash,
        created_at=api_key.created_at,
    )


def map_api_key_to_db(api_key: ApiKey) -> ApiKeyDB:
    return ApiKeyDB(
        id=api_key.id,
        user_id=api_key.user_id,
        name=api_key.name,
        key_hash=api_key.key_hash,
        created_at=api_key.created_at,
    )
