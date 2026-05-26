from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from prometheus_fastapi_instrumentator import Instrumentator
import os

from .middleware import LoggingMiddleware
from .routes import auth, students, monitoring
from .database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Student Management System", version="1.0.0")

# ── CORS (required for frontend to talk to backend) ──────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LoggingMiddleware)

Instrumentator().instrument(app).expose(app, endpoint="/metrics")

app.include_router(auth.router)
app.include_router(students.router)
app.include_router(monitoring.router)

# ── Serve frontend HTML ───────────────────────────────────────────────
FRONTEND_PATH = os.path.join(os.path.dirname(__file__), "..", "frontend.html")

@app.get("/ui", include_in_schema=False)
def serve_frontend():
    return FileResponse(FRONTEND_PATH)

@app.get("/")
def read_root():
    return {"message": "Welcome to Student Management System", "ui": "/ui"}

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "System is healthy"}
