import logging

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from eda_server.api import router as api_router
from eda_server.config import load_settings
from eda_server.db.dependency import get_db_session_factory
from eda_server.db.provider import DatabaseProvider

ALLOWED_ORIGINS = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:9000",
    "http://127.0.0.1",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:9000",
]

root_router = APIRouter()


@root_router.get("/ping")
def ping():
    return {"ping": "pong!"}


def setup_cors(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def setup_routes(app: FastAPI) -> None:
    app.include_router(root_router)
    app.include_router(api_router)


def setup_database(app: FastAPI) -> None:
    settings = app.state.settings
    provider = DatabaseProvider(settings.database_url)
    app.add_event_handler("shutdown", provider.close)
    app.dependency_overrides[
        get_db_session_factory
    ] = lambda: provider.session_factory


def configure_logging(app):
    settings = app.state.settings
    log_level = settings.log_level.upper()
    # The nested loggers will inherit parent logger log level.
    logging.getLogger("eda_server").setLevel(log_level)


# TODO(cutwater): Use dependency overrides.
# TODO(cutwater): Implement customizable ApplicationBuilder for testing.
def create_app() -> FastAPI:
    """Initialize FastAPI application."""
    settings = load_settings()
    app = FastAPI(
        title="Ansible Events API",
        description="API for Event Driven Automation",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )
    app.state.settings = settings

    configure_logging(app)
    setup_cors(app)
    setup_routes(app)

    setup_database(app)

    return app
