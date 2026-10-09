from fastapi import APIRouter
from backend.app.api.profiles import router as profiles_router
from backend.app.api.career import router as career_router
from backend.app.api.resources import router as resources_router
from backend.app.api.plans import router as plans_router
from backend.app.api.teaching import router as teaching_router
from backend.app.api.quiz import router as quiz_router
from backend.app.api.progress import router as progress_router
from backend.app.api.sandbox import router as sandbox_router

api_router = APIRouter(prefix="/api")
api_router.include_router(profiles_router)
api_router.include_router(career_router)
api_router.include_router(resources_router)
api_router.include_router(plans_router)
api_router.include_router(teaching_router)
api_router.include_router(quiz_router)
api_router.include_router(progress_router)
api_router.include_router(sandbox_router)
