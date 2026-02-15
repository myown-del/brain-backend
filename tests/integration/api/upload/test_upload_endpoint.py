import re
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient
from dishka import make_async_container, Provider, Scope, provide
from dishka.integrations.fastapi import setup_dishka

from brain.application.abstractions.storage.files import IFileStorage
from brain.application.interactors.upload_file import UploadFileInteractor
from brain.presentation.api.factory import create_bare_app
from brain.config.models import APIConfig


@pytest.fixture
def client(event_loop):
    api_config = APIConfig(
        internal_host="0.0.0.0",
        external_host="localhost",
        port=8080,
    )

    mock_file_storage = MagicMock(spec=IFileStorage)

    def upload_file_side_effect(content: bytes, object_name: str, content_type: str | None = None):
        return f"http://localhost:9000/test-bucket/{object_name}"

    mock_file_storage.upload.side_effect = upload_file_side_effect

    # Provider
    class MockProvider(Provider):
        scope = Scope.APP

        @provide
        def get_upload_file_interactor(self, file_storage: IFileStorage) -> UploadFileInteractor:
            return UploadFileInteractor(file_storage=file_storage)

        @provide(provides=IFileStorage)
        def get_file_storage(self) -> IFileStorage:
            return mock_file_storage

    # App
    app = create_bare_app(api_config)

    # Container
    container = make_async_container(MockProvider())
    setup_dishka(container=container, app=app)

    with TestClient(app) as client:
        yield client

    event_loop.run_until_complete(container.close())


def test_upload_image(client):
    files = {"file": ("test.jpg", b"content", "image/jpeg")}
    response = client.post(url="/api/upload/file", files=files)
    assert response.status_code == 200
    assert re.match(r"^http://localhost:9000/test-bucket/[0-9a-f-]+\.jpg$", response.json()["url"])


def test_upload_file_supports_non_image_content(client):
    files = {"file": ("report.pdf", b"content", "application/pdf")}
    response = client.post(url="/api/upload/file", files=files)
    assert response.status_code == 200
    assert re.match(r"^http://localhost:9000/test-bucket/[0-9a-f-]+\.pdf$", response.json()["url"])


def test_upload_file_without_extension(client):
    files = {"file": ("README", b"content", "text/plain")}
    response = client.post(url="/api/upload/file", files=files)
    assert response.status_code == 200
    assert re.match(r"^http://localhost:9000/test-bucket/[0-9a-f-]+\.bin$", response.json()["url"])


def test_upload_image_alias_remains_available(client):
    files = {"file": ("legacy.jpg", b"content", "image/jpeg")}
    response = client.post(url="/api/upload/image", files=files)
    assert response.status_code == 200
    assert re.match(r"^http://localhost:9000/test-bucket/[0-9a-f-]+\.jpg$", response.json()["url"])
