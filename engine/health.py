from __future__ import annotations

import json
from pathlib import Path
from typing import Literal, Any

from engine.docker import _run


HealthStatus = Literal[
    "healthy",
    "unhealthy",
    "starting",
    "none",        # container exists but no healthcheck / no metadata yet
    "not_found",   # service/container not present yet
]


def _extract_container(data: Any) -> Any | None:
    """
    Normalize docker compose ps --format json output
    to a single container representation.

    Docker may return:
    - list of dicts
    - dict keyed by service name
    - list of strings (container names)
    """
    if isinstance(data, list):
        return data[0] if data else None

    if isinstance(data, dict):
        return next(iter(data.values()), None)

    return None


def get_service_health(
    project: Path,
    service: str,
) -> HealthStatus:
    """
    Return the health status of a docker compose service.

    This function NEVER raises.
    """
    result = _run(
        [
            "docker",
            "compose",
            "ps",
            "--format",
            "json",
            service,
        ],
        cwd=project,
    )

    if not result.ok or not result.stdout:
        return "not_found"

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return "not_found"

    container = _extract_container(data)
    if container is None:
        return "not_found"

    # Container exists but Docker only returned its name (string)
    if isinstance(container, str):
        return "none"

    # Container metadata exists
    if isinstance(container, dict):
        health = container.get("Health")
        if health is None:
            return "none"
        return health  # healthy | unhealthy | starting

    return "not_found"
