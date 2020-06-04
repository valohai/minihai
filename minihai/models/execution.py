import json
import logging
import pathlib
from typing import Optional, Iterable
from uuid import UUID

import pydantic
import ulid2
from docker.models.containers import Container

import minihai.conf as conf
from minihai.lib.events import format_log_event
from minihai.models.base import BaseModel
from minihai.models.output import Output
from minihai.services.docker import get_container_logs

CONTAINER_EXIT_CODE_METADATA_KEY = "container_exit_code"
CONTAINER_FINAL_STATE_METADATA_KEY = "container_final_state"
ERROR_MESSAGE_METADATA_KEY = "error_message"

log = logging.getLogger(__name__)


def _existing_subpath(root: pathlib.Path, next: str) -> pathlib.Path:
    path = root / next
    path.mkdir(parents=True, exist_ok=True)
    return path


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

    @property
    def outputs_path(self) -> pathlib.Path:
        return _existing_subpath(self.path, "outputs")

    @property
    def config_path(self) -> pathlib.Path:
        return _existing_subpath(self.path, "config")

    @property
    def inputs_path(self) -> pathlib.Path:
        return _existing_subpath(self.path, "inputs")

    def get_log_path(self, name) -> pathlib.Path:
        return self.path / f"{name}.log"

    @property
    def all_json_log_path(self):
        return self.path / f"log.json"

    @property
    def status(self) -> str:
        error_message = self.metadata.get(ERROR_MESSAGE_METADATA_KEY)
        if error_message:
            return "error"
        final_state = self.metadata.get(CONTAINER_FINAL_STATE_METADATA_KEY)
        if final_state and final_state.get("Error"):
            return "error"
        container_exit_code = self.metadata.get(CONTAINER_EXIT_CODE_METADATA_KEY)
        if container_exit_code is not None:
            if container_exit_code == 0:
                return "complete"
            return "error"

        if self.metadata.get("container_id"):
            return "started"
        return "queued"

    @property
    def container(self) -> Optional[Container]:
        container_id = self.metadata.get("container_id")
        if not container_id:
            return None
        return conf.docker_client.containers.get(container_id=container_id)

    @classmethod
    def create(cls, data: ExecutionCreationData):
        id = str(ulid2.generate_ulid_as_uuid())
        counter = (
            cls.count() + 1
        )  # Not necessarily safe in highly concurrent situations.
        execution = cls.create_with_metadata(
            id=id, data={"counter": counter, **data.dict(),}
        )
        return execution

    def check_container_status(self: "Execution"):
        container = self.container
        if not container:
            return

        state = container.attrs["State"]
        status = state.get("Status")
        if status in ("exited", "dead"):
            if self.metadata.get("container_final_state") is None:
                self.update_metadata(
                    {
                        "container_exit_code": state.get("ExitCode"),
                        "container_final_state": state,
                    }
                )
            stdout_log_path = self.get_log_path("stdout")
            if not stdout_log_path.exists():
                stdout_log_path.write_bytes(
                    container.logs(stdout=True, stderr=False, timestamps=True)
                )
                log.info(f"{self.id}: Wrote stdout to {stdout_log_path}")
            stderr_log_path = self.get_log_path("stderr")
            if not stderr_log_path.exists():
                stderr_log_path.write_bytes(
                    container.logs(stdout=False, stderr=True, timestamps=True)
                )
                log.info(f"{self.id}: Wrote stderr to {stderr_log_path}")
            all_json_log_path = self.all_json_log_path
            if not all_json_log_path.exists():
                with all_json_log_path.open("w") as outf:
                    json.dump(get_container_logs(container), outf, indent=2)
                log.info(f"{self.id}: Wrote JSON log to {all_json_log_path}")

    def get_logs(self) -> Optional[list]:
        error_message = self.metadata.get(ERROR_MESSAGE_METADATA_KEY)
        if error_message:
            return [
                format_log_event(stream="stderr", message=error_message),
            ]
        if self.all_json_log_path.exists():
            with self.all_json_log_path.open("r") as fp:
                return json.load(fp)
        container = self.container
        if not container:
            return None
        return get_container_logs(container)

    def iterate_outputs(self) -> Iterable[Output]:
        for disk_path in self.outputs_path.rglob("*"):
            yield Output(
                name=disk_path.relative_to(self.outputs_path),
                path=str(disk_path.relative_to(conf.settings.data_path)),
                execution_id=self.id,
            )
