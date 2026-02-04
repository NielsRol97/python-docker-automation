from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass
import subprocess
from typing import Sequence


# -------------------------------------------------
# Types
# -------------------------------------------------
@dataclass(frozen=True)
class CommandResult:
    ok: bool
    stdout: str
    stderr: str
    exit_code: int

    @classmethod
    def success(cls, stdout: str = "") -> "CommandResult":
        return cls(True, stdout, "", 0)

    @classmethod
    def failure(cls, stderr: str, exit_code: int = -1, stdout: str = "") -> "CommandResult":
        return cls(False, stdout, stderr, exit_code)


# -------------------------------------------------
# Command runner (single choke point)
# -------------------------------------------------
def _run(
    cmd: Sequence[str],
    *,
    cwd: Path,
    timeout: int = 120,
) -> CommandResult:
    try:
        proc = subprocess.run(
            list(cmd),
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

        return CommandResult(
            ok=proc.returncode == 0,
            stdout=proc.stdout.strip(),
            stderr=proc.stderr.strip(),
            exit_code=proc.returncode,
        )

    except subprocess.TimeoutExpired as e:
        return CommandResult.failure(
            stderr="Command timed out",
            stdout=(e.stdout or "").strip(),
        )

    except FileNotFoundError:
        return CommandResult.failure(
            stderr=f"Command not found: {cmd[0]}",
        )


# -------------------------------------------------
# MySQL initialization marker
# -------------------------------------------------
def _mysql_marker(project: Path) -> Path:
    """
    Marker file indicating that MySQL has been initialized at least once.

    NOTE:
    This is a *local project marker*, not Docker state.
    It intentionally does NOT inspect volumes or containers.
    """
    return project / ".docker" / "mysql_initialized"


def mysql_volume_exists(project: Path) -> bool:
    """
    Return True if the project has previously initialized MySQL.

    This is a conservative signal used for warnings only.
    """
    return _mysql_marker(project).exists()


def mark_mysql_initialized(project: Path) -> None:
    """
    Mark MySQL as initialized for this project.

    This should only be called after a *successful* Docker up.
    """
    marker = _mysql_marker(project)
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.touch(exist_ok=True)


# -------------------------------------------------
# Docker Compose commands
# -------------------------------------------------
def docker_compose_up(project: Path) -> CommandResult:
    """
    Build and start the Docker Compose environment.

    This function does NOT:
    - run migrations
    - inspect container health
    - mutate project state

    It is intentionally narrow in responsibility.
    """
    return _run(
        [
            "docker",
            "compose",
            "-f",
            "docker-compose.yml",
            "up",
            "-d",
            "--build",
        ],
        cwd=project,
        timeout=300,  # builds can be slow
    )


def docker_compose_down(project: Path) -> CommandResult:
    """
    Stop and remove Docker Compose containers.

    Volumes are preserved by default.
    """
    return _run(
        [
            "docker",
            "compose",
            "-f",
            "docker-compose.yml",
            "down",
            "--remove-orphans",
        ],
        cwd=project,
    )
