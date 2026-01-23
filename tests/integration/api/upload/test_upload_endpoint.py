from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient
from dishka import make_async_container, Provider, Scope, provide
from dishka.integrations.fastapi import setup_dishka

from brain.presentation.api.factory import create_bare_app
from brain.config.models import Config, S3Config, APIConfig
from brain.infrastructure.s3.client import S3Client

@pytest.fixture
def client(event_loop):
    # Mock Config
    mock_config = MagicMock(spec=Config)
    mock_config.api = APIConfig(
        internal_host="0.0.0.0",
        external_host="localhost",
        port=8080,
    )
    mock_config.s3 = S3Config(
        external_host="http://localhost:9000",
        endpoint_url="http://test:9000",
        access_key_id="test",
        secret_access_key="test",
        bucket_name="test-bucket",
    )
    
    # Mock S3Client
    mock_s3_client = MagicMock(spec=S3Client)
    mock_s3_client.config = mock_config.s3
    mock_s3_client.upload_file.return_value = "http://test:9000/test-bucket/image.jpg"
    
    # Provider
    class MockProvider(Provider):
        scope = Scope.APP
        
        @provide
        def get_s3_client(self) -> S3Client:
            return mock_s3_client
            
        @provide
        def get_s3_config(self) -> S3Config:
            return mock_config.s3

    # App
    app = create_bare_app(mock_config.api)
    
    # Container
    container = make_async_container(MockProvider())
    setup_dishka(container=container, app=app)
    
    with TestClient(app) as client:
        yield client

    event_loop.run_until_complete(container.close())


def test_upload_image(client):
    files = {'file': ('test.jpg', b'content', 'image/jpeg')}
    response = client.post(url="/api/upload/image", files=files)
    assert response.status_code == 200
    assert response.json() == {"url": "http://localhost:9000/test-bucket/image.jpg"}
