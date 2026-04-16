import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.cache.redis_cache import cache
from app.core.config import settings
from app.db.bootstrap import bootstrap_database

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager"""
    # Startup — tolerate DB bootstrap errors so the API still starts
    try:
        bootstrap_database()
    except Exception as exc:
        logger.error("Database bootstrap failed, continuing without it: %s", exc, exc_info=True)
    await cache.connect()

    yield

    # Shutdown
    await cache.disconnect()


app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

settings.media_path.mkdir(parents=True, exist_ok=True)
app.mount(settings.MEDIA_URL, StaticFiles(directory=settings.media_path), name="media")

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {"message": "Redline API running"}
