from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .routes import activities, boroughs, health, stats, users


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(title=settings.app_name)

    # Basic CORS setup for local/mobile dev; tighten later as needed.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(health.router)
    app.include_router(boroughs.router)
    app.include_router(users.router)
    app.include_router(activities.router)
    app.include_router(stats.router)

    return app


app = create_app()


