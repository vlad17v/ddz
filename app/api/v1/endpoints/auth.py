from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Form
from fastapi import HTTPException
from fastapi import Request
from fastapi import status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from starlette.responses import HTMLResponse

from app.core.templates import templates
from app.dependencies import get_auth_service
from app.dependencies import get_current_active_user
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/token", response_class=HTMLResponse)
async def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        await auth_service.authenticate(form_data.username, form_data.password)
    except HTTPException:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Incorrect username or password"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=f"Bearer {form_data.username}", httponly=True)
    return response


@router.get("/logout")
async def logout(
    current_user=Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    response = RedirectResponse("/auth/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    await auth_service.logout(current_user.name)
    return response


@router.get("/login", status_code=status.HTTP_200_OK)
async def get_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/users/me")
async def read_users_me(current_user=Depends(get_current_active_user)):
    return {"name": current_user.name, "disabled": current_user.disabled}


@router.get("/register", response_class=HTMLResponse)
async def get_register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register", response_class=HTMLResponse)
async def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        await auth_service.register(username, password)
    except HTTPException:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Username already registered"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
