from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.api import auth as auth_router
from app.api import exams as exams_router
from app.api import rubric as rubric_router
from app.api import policies as policies_router
from app.api import copies as copies_router
from app.api import grading as grading_router
from app.api import exports as exports_router

configure_logging()

app = FastAPI(title="Exam Grader API", version="0.1.0")

_origins = get_settings().cors_origins_list
_allow_all = _origins == ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    # L'auth se fait par token Bearer (pas de cookie) : avec "*", on désactive
    # allow_credentials (exigence de la spec CORS) sans perte de fonctionnalité.
    allow_credentials=not _allow_all,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


app.include_router(auth_router.router)
app.include_router(exams_router.router)
app.include_router(rubric_router.router)
app.include_router(policies_router.router)
app.include_router(copies_router.router)
app.include_router(grading_router.router)
app.include_router(exports_router.router)
