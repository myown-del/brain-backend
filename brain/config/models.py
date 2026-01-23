from dataclasses import dataclass, field
from enum import Enum

from brain.application.abstractions.config.models import IDatabaseConfig, INeo4jConfig


@dataclass
class APIConfig:
    internal_host: str
    external_host: str
    port: int
    auto_reload: bool = True
    allowed_origins: list[str] = field(default_factory=lambda: ["*"])
    workers: int = 1


@dataclass
class DatabaseConfig(IDatabaseConfig):
    host: str
    port: int
    database: str
    user: str
    password: str
    engine: str = "postgresql+asyncpg"

    @property
    def uri(self) -> str:
        return f"{self.engine}://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class RedisConfig:
    host: str
    port: int
    db: int
    password: str

    @property
    def uri(self) -> str:
        return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"


@dataclass
class Neo4jConfig(INeo4jConfig):
    host: str
    port: int
    user: str
    password: str
    database: str = "neo4j"
    scheme: str = "neo4j"

    @property
    def uri(self) -> str:
        return f"{self.scheme}://{self.host}:{self.port}"


@dataclass
class BotConfig:
    token: str


class EnvironmentType(Enum):
    DEVELOPMENT = "dev"
    TESTING = "test"
    PRODUCTION = "prod"


@dataclass
class AuthenticationConfig:
    admin_token: str
    # JWT settings
    secret_key: str
    access_token_lifetime: int = 3600
    refresh_token_lifetime: int = 86400
    algorithm: str = "HS256"


@dataclass
class S3Config:
    external_host: str
    endpoint_url: str
    access_key_id: str
    secret_access_key: str
    bucket_name: str
    region_name: str = "us-east-1"


@dataclass
class Config:
    api: APIConfig
    auth: AuthenticationConfig
    db: DatabaseConfig
    redis: RedisConfig
    neo4j: Neo4jConfig
    s3: S3Config
    bot: BotConfig
    environment: EnvironmentType
    logging_level: str = "INFO"
