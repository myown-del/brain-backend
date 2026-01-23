from fastapi import FastAPI, APIRouter

from brain.config.models import APIConfig
from .healthcheck import get_router as get_healthcheck_router
from .tgbot import get_router as get_tgbot_router
from .auth import get_router as get_auth_router
from .users import get_router as get_users_router
from .test import router as test_router
from .notes import get_router as get_notes_router
from .graph import get_router as get_graph_router
from .upload import get_router as get_upload_router


def register_routes(app: FastAPI, config: APIConfig):
    root_router = APIRouter(prefix="/api")
    root_router.include_router(get_tgbot_router(config))
    root_router.include_router(get_healthcheck_router())
    root_router.include_router(get_auth_router())
    root_router.include_router(get_users_router())
    root_router.include_router(get_notes_router())
    root_router.include_router(get_graph_router())
    root_router.include_router(get_upload_router())
    root_router.include_router(test_router)

    app.include_router(root_router)
