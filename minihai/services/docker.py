import logging
import shlex
from operator import itemgetter
from typing import Dict, List, Optional

from docker.errors import ImageNotFound, APIError
from docker.models.containers import Container
from docker.types import Mount

import minihai.conf as conf
from minihai.lib.events import format_log_event

log = logging.getLogger(__name__)


class BootError(RuntimeError):
    pass


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
    mounts = list(mounts) + get_container_mounts(container_name, tarball_root)

    try:
        docker_image = conf.docker_client.images.get(image)
    except ImageNotFound:
        log.info(f"Image {image} not found locally, pulling it.")
        try:
            docker_image = conf.docker_client.images.pull(image)
        except APIError as ae:
            raise BootError(f"Could not pull image {image}.\n{ae}") from ae
    log.info(f"Image {image}: {docker_image.id}")

    log.info(f"Creating container {container_name}...")
    container: Container = conf.docker_client.containers.create(
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


def get_container_mounts(container_name: str, tarball_root: str):
    mounts = []
    # Ensure the tarball extraction root exists in the image by mounting it as a volume.
    # We can't run a mkdir before the container runs and we also don't want to race against
    # the injection of those files.
    volume_name = container_name + "-root"
    log.info(f"Creating volume {volume_name}...")
    in_volume = conf.docker_client.volumes.create(name=volume_name)
    mounts.append(Mount(target=tarball_root, source=in_volume.name, type="volume",))
    # Then add in any configured RW/RO mounts.
    for read_only, map in [
        (False, conf.settings.mounts),
        (True, conf.settings.read_only_mounts),
    ]:
        for source, destination in map.items():
            mounts.append(
                Mount(
                    target=destination, source=source, read_only=read_only, type="bind",
                )
            )
    return mounts


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
                format_log_event(
                    stream=stream, message=content, time=timestamp.strip("Z")
                )
            )
    events.sort(key=itemgetter("time"))
    return events
