import datetime
from uuid import UUID

from fastapi import Path, APIRouter

from minihai import consts as consts
from minihai.app.utils import make_list_response
from minihai.models.commit import Commit
from minihai.models.execution import Execution, ExecutionCreationData
from minihai.services.execution import start_execution

router = APIRouter()


def convert_execution(execution: Execution) -> dict:
    return {
        **execution.metadata,
        "duration": None,
        "events": None,
        "urls": {"display": None},
        "status": execution.status,
    }


@router.get("/api/v0/executions/")
def read_executions():
    execution_datas = [
        convert_execution(execution) for execution in Execution.iterate_instances()
    ]
    execution_datas.sort(key=lambda e: e["ctime"])
    for counter, execution_data in enumerate(execution_datas, 1):
        execution_data["counter"] = counter
    execution_datas.reverse()
    return make_list_response(execution_datas)


@router.get("/api/v0/executions/{execution_id}/")
def get_execution_detail(execution_id: UUID = Path(default=None),):
    execution = Execution.load(id=execution_id)
    execution.check_container_status()
    return convert_execution(execution)


@router.get("/api/v0/executions/{execution_id}/events/")
def get_execution_events(execution_id: UUID = Path(default=None),):
    execution = Execution.load(id=execution_id)
    execution.check_container_status()
    events = execution.get_logs()
    if not events:
        events = [
            {
                "stream": "status",
                "message": "No events available...",
                "time": datetime.datetime.now().isoformat(),
            },
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
    start_execution(exec)  # TODO: absolutely no queuing here :)
    return exec.metadata
