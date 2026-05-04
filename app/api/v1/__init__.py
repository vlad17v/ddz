from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.flowers import router as flowers_router
from app.api.v1.endpoints.tags import router as tags_router
from app.api.v1.endpoints.todos import router as todos_router

api_router = APIRouter()
api_router.include_router(todos_router)
api_router.include_router(auth_router)
api_router.include_router(flowers_router)
api_router.include_router(tags_router)