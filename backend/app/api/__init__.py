from app.api.auth import router as auth_router
from app.api.chapters import router as chapters_router
from app.api.words import router as words_router
from app.api.vocabulary import router as vocabulary_router
from app.api.settings import router as settings_router
from app.api.exams import router as exams_router

__all__ = ["auth_router", "chapters_router", "words_router", "vocabulary_router", "settings_router", "exams_router"]
