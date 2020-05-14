from uuid import UUID

import pydantic
import ulid2

from minihai.models.base import BaseModel


class ExecutionCreationData(pydantic.BaseModel):
    commit: str
    project: UUID
    inputs: dict
    parameters: dict
    environment_variables: dict
    step: str
    image: str
    title: str = ""
    environment: UUID


class Execution(BaseModel):
    kind = "execution"
    path_group_len = 8

    @classmethod
    def create(cls, data: ExecutionCreationData):
        id = str(ulid2.generate_ulid_as_uuid())
        execution = cls.create_with_metadata(id=id, data={**data.dict(),})
        return execution
