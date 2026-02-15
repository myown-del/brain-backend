from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import AsyncMock

import pytest
from dishka import make_async_container, Provider, Scope, provide
from dishka.integrations.fastapi import setup_dishka
from fastapi.testclient import TestClient

from brain.application.abstractions.repositories.s3_files import IS3FilesRepository
from brain.application.interactors.get_file import GetFileInteractor
from brain.config.models import APIConfig, S3Config
from brain.domain.entities.s3_file import S3File
from brain.presentation.api.factory import create_bare_app


@pytest.fixture
def client(event_loop):
    # setup: api and s3 config used by URL builder
    api_config = APIConfig(
        internal_host="0.0.0.0",
        external_host="localhost",
        port=8080,
    )
    s3_config = S3Config(
        external_host="http://files.example.com",
        endpoint_url="http://localhost:9000",
        access_key_id="key",
        secret_access_key="secret",
        bucket_name="test-bucket",
    )
    file_id = uuid4()
    existing_file = S3File(
        id=file_id,
        name="report.pdf",
        path="docs/report.pdf",
        content_type="application/pdf",
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )

    # setup: repository returns file by id
    mock_s3_files_repo = AsyncMock(spec=IS3FilesRepository)

    async def get_by_id(file_id):
        if file_id == existing_file.id:
            return existing_file
        return None

    mock_s3_files_repo.get_by_id.side_effect = get_by_id

    # setup: dishka provider for interactor + dependencies
    class MockProvider(Provider):
        scope = Scope.APP

        @provide
        def get_get_file_interactor(self, s3_files_repo: IS3FilesRepository, s3_config: S3Config) -> GetFileInteractor:
            return GetFileInteractor(s3_files_repo=s3_files_repo, s3_config=s3_config)

        @provide(provides=IS3FilesRepository)
        def get_s3_files_repo(self) -> IS3FilesRepository:
            return mock_s3_files_repo

        @provide
        def get_s3_config(self) -> S3Config:
            return s3_config

    # setup: app and DI container
    app = create_bare_app(api_config)
    container = make_async_container(MockProvider())
    setup_dishka(container=container, app=app)

    with TestClient(app) as client:
        yield client, existing_file

    event_loop.run_until_complete(container.close())


def test_get_file_success(client):
    # setup: use existing stored file id
    client, existing_file = client

    # action: get file by id
    response = client.request(method="GET", url=f"/api/file/{existing_file.id}")

    # check: file payload contains dynamic URL and metadata
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(existing_file.id)
    assert payload["name"] == existing_file.name
    assert payload["path"] == existing_file.path
    assert payload["url"] == "http://files.example.com/docs/report.pdf"
    assert payload["content_type"] == existing_file.content_type
    assert payload["created_at"] == existing_file.created_at.isoformat().replace("+00:00", "Z")


def test_get_file_not_found(client):
    # setup: use random id that does not exist
    client, _ = client
    missing_id = uuid4()

    # action: get file by id
    response = client.request(method="GET", url=f"/api/file/{missing_id}")

    # check: endpoint returns 404 with clear message
    assert response.status_code == 404
    assert response.json()["detail"] == "File not found"
