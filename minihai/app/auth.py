import datetime
import hashlib

import jwt
from fastapi import HTTPException, Depends
from fastapi.security.utils import get_authorization_scheme_param
from jwt import PyJWTError
from starlette import status
from starlette.requests import Request

from minihai import conf

JWT_ALGORITHM = "HS256"


async def minihai_auth(request: Request):
    if not conf.settings.auth:
        return True  # no auth, always OK
    return await check_jwt_auth(request)


async def check_jwt_auth(request: Request) -> str:
    authorization: str = request.headers.get("Authorization")
    scheme, token = get_authorization_scheme_param(authorization)
    if scheme.lower() != "token":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid auth scheme {scheme}",
            headers={"WWW-Authenticate": "Token"},
        )
    try:
        payload = jwt.decode(
            token, key=conf.settings.jwt_secret, algorithms=[JWT_ALGORITHM]
        )
        username: str = payload.get("sub")
        password = conf.settings.auth.get(username)
        if not (password and generate_pha(password) == payload.get("pha")):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid user {username}",
                headers={"WWW-Authenticate": "Token"},
            )
        return username
    except PyJWTError as je:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token decode error: {je}",
            headers={"WWW-Authenticate": "Token"},
        )


def create_access_token(data: dict):
    return jwt.encode(
        {**data, "iat": datetime.datetime.now(), "iss": "minihai"},
        key=conf.settings.jwt_secret,
        algorithm=JWT_ALGORITHM,
    )


def create_user_access_token(username: str):
    password = conf.settings.auth[username]
    return create_access_token({"sub": username, "pha": generate_pha(password),})


def generate_pha(password):
    return hashlib.sha1(password.encode()).hexdigest()


MinihaiAuth = Depends(minihai_auth)
