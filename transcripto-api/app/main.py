from fastapi import FastAPI
from app.routes import upload, status

app = FastAPI(
    title="Transcripto API",
    description="Async audio transcription platform — CMPE 281",
    version="1.0.0",
)

app.include_router(upload.router, tags=["jobs"])
app.include_router(status.router, tags=["jobs"])


@app.get("/health")
async def health():
    return {"status": "ok"}
