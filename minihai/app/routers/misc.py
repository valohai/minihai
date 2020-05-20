from fastapi import APIRouter

from minihai import consts as consts
from minihai.app.utils import make_list_response

router = APIRouter()


@router.get("/api/v0/users/me/")
def read_user():
    return consts.EXPANDED_USER_DATA


@router.get("/api/v0/projects/")
def read_projects():
    return make_list_response([consts.PROJECT_DATA,])


@router.get(f"/api/v0/projects/{consts.PROJECT_ID}/")
def read_project():
    return consts.PROJECT_DATA


@router.get("/api/v0/environments/")
def read_environments():
    return make_list_response([consts.ENVIRONMENT_DATA,])
