import secrets

from fastapi import APIRouter, Response, HTTPException, Form

import minihai
from minihai import conf
from minihai.app.auth import create_access_token, create_user_access_token
from minihai.art import BANNER

router = APIRouter()


@router.get("/")
def read_root():
    return Response(
        f"{BANNER}\n\nVersion {minihai.__version__}", media_type="text/plain"
    )


@router.get("/api/v0/server/")
def get_server_info():
    return {
        "flavor": "minihai",
        "version": minihai.__version__,
    }


@router.post("/api/v0/get-token/")
def get_token(username: str = Form(None), password: str = Form(None)):
    if not conf.settings.auth:
        # This token will become invalid if auth is turned on.
        return {
            "token": create_access_token({"sub": None}),
        }
    correct_password = conf.settings.auth.get(username)
    if not correct_password:
        raise HTTPException(400, {"error": "Invalid Minihai username"})
    if not secrets.compare_digest(password, correct_password):
        raise HTTPException(400, {"error": "Invalid Minihai password"})

    return {
        "token": create_user_access_token(username),
    }
