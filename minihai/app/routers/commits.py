from typing import Optional
from uuid import UUID

from fastapi import Path, HTTPException, UploadFile, File, APIRouter

from minihai import consts as consts
from minihai.models.base import DoesNotExist
from minihai.models.commit import Commit

router = APIRouter()


@router.get("/api/v0/commits/{id}/")
def read_commit(id: str = Path(default=None)):
    try:
        commit = Commit.load(id)
        return commit.metadata
    except DoesNotExist:
        raise HTTPException(404, "Commit not found")


@router.post("/api/v0/projects/{project_id}/import-package/")
def import_package(
    project_id: UUID = Path(default=None),
    data: UploadFile = File(default=None),
    description: Optional[str] = "",
):
    assert project_id == consts.PROJECT_ID
    commit = Commit.create_from_data(data=data, description=description)
    return commit.metadata
