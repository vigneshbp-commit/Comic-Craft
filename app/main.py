import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import (
    EXPORTS_DIR,
    PANELS_DIR,
    STATIC_DIR,
    settings,
)
from app.routes import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("comiccraft")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event handler for directory preparation and teardown."""
    logger.info("Initializing %s in %s mode...", settings.APP_NAME, settings.APP_ENV)
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    PANELS_DIR.mkdir(parents=True, exist_ok=True)
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    yield
    logger.info("Shutting down %s...", settings.APP_NAME)


def create_app() -> FastAPI:
    """Application factory for ComicCraft."""
    app = FastAPI(
        title="ComicCraft - AI Comic Story Creator",
        description="Generate personalized multi-panel comic book stories and illustrations with Google Gemini & Stable Diffusion.",
        version="1.0.0",
        lifespan=lifespan
    )

    # Mount static files
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # Register routes
    app.include_router(router)

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
