from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import AuthServiceDep, CurrentUser, DbDep
from app.api.schemas import RegisterRequest, TokenOut, UserOut
from app.core.security import create_access_token
from app.models.Listener import Listener
from app.models.User import User

router = APIRouter(tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, service: AuthServiceDep, db: DbDep) -> Listener:
    """Регистрация нового слушателя. Роль администратора выдаётся только вручную."""
    user = service.register(data.email, data.username, data.password)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenOut)
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: AuthServiceDep,
) -> TokenOut:
    """Вход по username или email. Тело запроса — form-data (username, password)."""
    user = service.authenticate(form.username, form.password)
    if user is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenOut(access_token=create_access_token(user.id, user.type))


@router.get("/users/me", response_model=UserOut)
def read_me(user: CurrentUser) -> User:
    return user
