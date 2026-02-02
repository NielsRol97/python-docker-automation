from __future__ import annotations
from pathlib import Path
import subprocess


def _run(cmd: list[str], cwd: Path) -> tuple[bool, str]:
    try:
        p = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False,
        )
        out = (p.stdout or "") + ("\n" + p.stderr if p.stderr else "")
        return p.returncode == 0, out.strip()
    except Exception as e:
        return False, str(e)


def mysql_volume_exists(project_path: Path) -> bool:
    """
    Detect whether a MySQL data volume already exists for this project.
    """
    volume_marker = project_path / ".docker" / "mysql_initialized"
    return volume_marker.exists()


def mark_mysql_initialized(project_path: Path) -> None:
    """
    Mark MySQL as initialized (called after successful startup).
    """
    marker = project_path / ".docker" / "mysql_initialized"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.touch(exist_ok=True)


def docker_compose_up(project_path: Path) -> tuple[bool, str]:
    return _run(
        ["docker", "compose", "-f", "docker-compose.yml", "up", "-d", "--build"],
        cwd=project_path,
    )


def docker_compose_down(project_path: Path) -> tuple[bool, str]:
    return _run(
        ["docker", "compose", "-f", "docker-compose.yml", "down", "--remove-orphans"],
        cwd=project_path,
    )
