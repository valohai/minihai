import logging
from uuid import UUID

from fastapi import Path, APIRouter

from minihai import consts as consts
from minihai.app.utils import make_list_response
from minihai.models.commit import Commit
from minihai.models.execution import (
    Execution,
    ExecutionCreationData,
    ERROR_MESSAGE_METADATA_KEY,
)
from minihai.lib.events import format_log_event
from minihai.services.execution import start_execution

router = APIRouter()

log = logging.getLogger(__name__)


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
    execution_datas.sort(key=lambda e: e["ctime"], reverse=True)
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
            format_log_event(stream="status", message="No events available..."),
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
    execution = Execution.create(data=body)
    try:
        start_execution(execution)  # TODO: absolutely no queuing here :)
    except Exception as exc:
        log.error(f"Could not start execution {execution.id}", exc_info=True)
        execution.update_metadata(
            {ERROR_MESSAGE_METADATA_KEY: str(exc),}
        )

    return execution.metadata
