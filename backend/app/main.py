from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import settings

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

settings.media_path.mkdir(parents=True, exist_ok=True)
app.mount(settings.MEDIA_URL, StaticFiles(directory=settings.media_path), name="media")

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {"message": "Redline API running"}
