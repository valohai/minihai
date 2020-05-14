import logging
import shlex
from operator import itemgetter
from typing import Dict, List, Optional

from docker.models.containers import Container
from docker.types import Mount

from minihai.conf import docker_client

log = logging.getLogger(__name__)


# Borrowed from VHNB :)
def boot_container(
    *,
    command: str,
    container_name: str,
    environment_variables: Dict[str, str],
    image: str,
    labels: Dict[str, str],
    tarball_filenames: List[str],
    tarball_root: Optional[str] = None,
    tarball_chown_stanza: Optional[str] = None,
    mounts: list,
):
    # Ensure the tarball extraction root exists in the image by mounting it as a volume.
    # We can't run a mkdir before the container runs and we also don't want to race against
    # the injection of those files.
    volume_name = container_name + "-root"
    log.info(f"Creating volume {volume_name}...")
    in_volume = docker_client.volumes.create(name=volume_name)
    mounts.append(Mount(target=tarball_root, source=in_volume.name, type="volume",))

    log.info(f"Creating container {container_name}...")
    container: Container = docker_client.containers.create(
        command=command,
        environment=environment_variables,
        image=image,
        labels=labels,
        mounts=mounts,
        name=container_name,
        network_mode="bridge",
    )

    did_inject = inject_tarballs(
        container=container,
        tarball_root=tarball_root,
        tarball_filenames=tarball_filenames,
    )
    log.info(f"Starting container {container.id}...")
    container.start()
    if tarball_chown_stanza and did_inject:
        log.info(f"Running recursive chown...")
        cmd = " ".join(
            [
                "chown",
                "-R",
                shlex.quote(tarball_chown_stanza),
                shlex.quote(tarball_root),
            ]
        )
        container.exec_run(cmd, user="root")
    container.reload()
    return container


def inject_tarballs(
    *, container: Container, tarball_root: str, tarball_filenames: List[str]
) -> bool:
    if not tarball_filenames:
        return False
    for filename in tarball_filenames:
        log.info(f"Injecting {filename} in {tarball_root}...")
        with open(filename, "rb") as infp:
            container.put_archive(tarball_root, data=infp)
    return True


def get_container_logs(container: Container) -> List[dict]:
    events = []
    for stream in ("stdout", "stderr"):
        for line in container.logs(
            stdout=(stream == "stdout"), stderr=(stream == "stderr"), timestamps=True
        ).split(b"\n"):
            line = line.decode("utf-8", errors="replace")
            if not line:
                continue
            timestamp, content = line.split(" ", 1)
            events.append(
                {"stream": stream, "message": content, "time": timestamp.strip("Z")}
            )
    events.sort(key=itemgetter("time"))
    return events
