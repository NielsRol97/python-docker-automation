from __future__ import annotations

from pathlib import Path
import time

from engine.templates import (
    docker_compose_yml,
    nginx_default_conf,
    php_dockerfile,
    php_ini_overrides,
)
from engine.fs import ensure_file, ensure_directory, safe_backup
from engine.laravel import ensure_env_defaults
from engine.docker_health import get_service_health


# -------------------------------------------------
# Errors
# -------------------------------------------------
class ProjectValidationError(RuntimeError):
    pass


# -------------------------------------------------
# Preflight validation
# -------------------------------------------------
def validate_project_for_docker(project: Path) -> None:
    """
    Ensure the project contains the minimum required files
    before generating Docker configuration.
    """
    required_files = [
        project / "artisan",
        project / "composer.json",
    ]

    missing = [p.name for p in required_files if not p.is_file()]

    if missing:
        raise ProjectValidationError(
            "Missing required project files: "
            + ", ".join(missing)
        )


# -------------------------------------------------
# Use case: generate docker setup
# -------------------------------------------------
def generate_docker_files(
    project: Path,
    *,
    overwrite_compose: bool = True,
    update_env: bool = True,
) -> list[str]:
    """
    Generate all Docker-related files for a Laravel project.

    This function intentionally makes docker-compose.yml authoritative.
    Existing compose files are backed up and overridden to prevent
    accidental Docker Compose merging.
    """
    # -------------------------------------------------
    # Preflight (NO side effects)
    # -------------------------------------------------
    validate_project_for_docker(project)

    actions: list[str] = []

    # -------------------------------------------------
    # Directory structure
    # -------------------------------------------------
    docker_dir = project / "docker"
    nginx_dir = docker_dir / "nginx"
    php_dir = docker_dir / "php"

    for directory in (docker_dir, nginx_dir, php_dir):
        ensure_directory(directory)

    actions.append("Ensured docker/, nginx/, php/ directories")

    # -------------------------------------------------
    # Static config files
    # -------------------------------------------------
    _ensure_static_file(
        nginx_dir / "default.conf",
        nginx_default_conf(),
        actions,
        "Generated nginx default.conf",
    )

    _ensure_static_file(
        php_dir / "Dockerfile",
        php_dockerfile(),
        actions,
        "Generated PHP Dockerfile",
    )

    _ensure_static_file(
        php_dir / "zz-overrides.ini",
        php_ini_overrides(),
        actions,
        "Generated PHP ini overrides",
    )

    # -------------------------------------------------
    # docker-compose.yml (authoritative)
    # -------------------------------------------------
    compose_path = project / "docker-compose.yml"
    override_path = project / "docker-compose.override.yml"

    if overwrite_compose:
        if compose_path.exists():
            backup = safe_backup(compose_path)
            actions.append(f"Backed up docker-compose.yml → {backup.name}")

        if override_path.exists():
            backup = safe_backup(override_path)
            override_path.unlink()
            actions.append(
                f"Removed docker-compose.override.yml "
                f"(backup → {backup.name})"
            )

    compose_path.write_text(
        docker_compose_yml(project.name),
        encoding="utf-8",
    )
    actions.append("Generated docker-compose.yml (authoritative)")

    # -------------------------------------------------
    # .env defaults
    # -------------------------------------------------
    if update_env:
        changed_keys = ensure_env_defaults(project)
        if changed_keys:
            actions.append(
                "Updated .env keys: " + ", ".join(sorted(changed_keys))
            )
        else:
            actions.append("No .env changes required")

    return actions


# -------------------------------------------------
# Helpers
# -------------------------------------------------
def _ensure_static_file(
    path: Path,
    content: str,
    actions: list[str],
    message: str,
) -> None:
    ensure_file(path, content)
    actions.append(message)


# -------------------------------------------------
# Use case: wait for docker service health
# -------------------------------------------------
def wait_for_service_healthy(
    project: Path,
    service: str,
    *,
    timeout: int = 60,
    poll_interval: int = 3,
) -> bool:
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        health = get_service_health(project, service)

        if health in ("healthy", "none"):
            return True

        time.sleep(poll_interval)

    return False
