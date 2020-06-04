import logging
import shlex

from docker.models.containers import Container
from docker.types import Mount

from minihai.models.commit import Commit
from minihai.models.execution import Execution, ExecutionCreationData
from minihai.services.docker import boot_container

log = logging.getLogger(__name__)


def write_config_files(execution: Execution) -> None:
    config_path = execution.config_path
    for name in ("parameters", "config", "inputs"):
        # Just emulate the Valohai configuration files without content for the time being.
        (config_path / f"{name}.yaml").write_text("{}")
        (config_path / f"{name}.json").write_text("{}")


def start_execution(execution: Execution) -> Container:
    metadata = execution.metadata
    if "container_id" in metadata:
        raise NotImplementedError("Already have a container ID")
    execution_info: ExecutionCreationData = ExecutionCreationData.parse_obj(metadata)
    commit = Commit.load(id=execution_info.commit)
    config = commit.load_config()
    step = config.get_step_by(name=execution_info.step)
    environment_variables = {
        name: ev.default
        for (name, ev) in step.environment_variables.items()
        if ev.default
    }
    command = " && ".join(
        step.build_command(parameter_values=execution_info.parameters)
    )
    command = f"sh -c {shlex.quote(command)}"
    write_config_files(execution)
    container = boot_container(
        command=command,
        container_name=f"minihai-{execution.id}",
        environment_variables=environment_variables,
        image=qualify_image_name(execution_info),
        labels={},
        tarball_filenames=[commit.tarball_path],
        tarball_root="/valohai/repository/",
        tarball_chown_stanza=None,
        mounts=[
            Mount(
                target="/valohai/outputs",
                source=str(execution.outputs_path.absolute()),
                read_only=False,
                type="bind",
            ),
            Mount(
                target="/valohai/config",
                source=str(execution.config_path.absolute()),
                read_only=True,
                type="bind",
            ),
            Mount(
                target="/valohai/inputs",
                source=str(execution.inputs_path.absolute()),
                read_only=True,
                type="bind",
            ),
        ],
    )
    execution.update_metadata({"container_id": container.id})
    return container


def qualify_image_name(execution_info):
    image = execution_info.image
    # TODO: should this be more robust?
    if ":" not in image:
        image = f"{image}:latest"
    return image
