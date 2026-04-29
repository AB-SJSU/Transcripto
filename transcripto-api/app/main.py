from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from starlette.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import upload, status, auth

app = FastAPI(
    title="Transcripto API",
    description="Async audio transcription platform — CMPE 281",
    version="1.0.0",
)

@app.middleware("http")
async def force_https(request: Request, call_next):
    if request.headers.get("x-forwarded-proto") == "http":
        url = request.url.replace(scheme="https")
        return RedirectResponse(url=str(url), status_code=301)
    return await call_next(request)


if settings.cors_origins_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

app.include_router(auth.router)
app.include_router(upload.router, tags=["jobs"])
app.include_router(status.router, tags=["jobs"])


@app.get("/health")
async def health():
    return {"status": "ok"}
