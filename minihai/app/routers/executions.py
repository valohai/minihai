from uuid import UUID

from fastapi import Path, APIRouter

from minihai import consts as consts
from minihai.app.utils import make_list_response
from minihai.models.commit import Commit
from minihai.models.execution import Execution, ExecutionCreationData

router = APIRouter()


@router.get("/api/v0/executions/")
def read_executions():
    execution_datas = []
    for execution in Execution.iterate_instances():
        data = {
            **execution.metadata,
            "duration": None,
            "events": None,
            "urls": {"display": None,},
        }
        execution_datas.append(data)
    execution_datas.sort(key=lambda e: e["ctime"])
    for counter, execution_data in enumerate(execution_datas, 1):
        execution_data["counter"] = counter
    execution_datas.reverse()
    return make_list_response(execution_datas)


@router.get("/api/v0/executions/{execution_id}/events/")
def get_execution_events(execution_id: UUID = Path(default=None),):
    execution = Execution.load(id=execution_id)
    message = "haha blah"
    events = [
        {"stream": "status", "message": message, "time": "2017-04-04T11:38:28.444000"},
        {"stream": "stderr", "message": message, "time": "2017-04-04T11:39:28.444000"},
        {"stream": "stdout", "message": message, "time": "2017-04-04T11:41:28.444000"},
    ]
    return {
        "total": len(events),
        "limit": 2000,
        "truncated": False,
        "events": events,
    }


@router.post("/api/v0/executions/", status_code=201)
def create_execution(body: ExecutionCreationData):
    assert body.project == consts.PROJECT_ID
    assert body.environment == consts.ENVIRONMENT_ID
    if body.parameters:
        raise NotImplementedError("Parameters not supported")
    if body.inputs:
        raise NotImplementedError("Inputs not supported")
    Commit.load(id=body.commit)  # simply asserts the commit exists
    exec = Execution.create(data=body)
    return exec.metadata
