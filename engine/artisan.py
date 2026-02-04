from __future__ import annotations

from pathlib import Path
from typing import Sequence

from engine.docker import CommandResult, _run


def artisan(
    project: Path,
    args: Sequence[str],
    *,
    timeout: int = 120,
) -> CommandResult:
    """
    Run a Laravel artisan command inside the app container.

    This function assumes:
    - Docker Compose services are already running
    - The service name is `app`
    - PHP and artisan are available in the container

    It does NOT:
    - Start containers
    - Retry failures
    - Interpret artisan output
    """
    if not args:
        return CommandResult.failure(
            stderr="No artisan command provided",
        )

    return _run(
        [
            "docker",
            "compose",
            "exec",
            "-T",  # no TTY (important for Streamlit / CI)
            "app",
            "php",
            "artisan",
            *args,
        ],
        cwd=project,
        timeout=timeout,
    )
