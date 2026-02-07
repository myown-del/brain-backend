from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CreateApiKeySchema(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class ApiKeySchema(BaseModel):
    id: UUID
    name: str
    key: str
    created_at: datetime


class ReadApiKeySchema(BaseModel):
    id: UUID
    name: str
    created_at: datetime


class ApiKeyValidationSchema(BaseModel):
    is_valid: bool
