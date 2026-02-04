from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from engine.docker import (
    CommandResult,
    docker_compose_up,
    docker_compose_down,
    mark_mysql_initialized,
)
from engine.artisan import artisan
from engine.app import wait_for_service_healthy
from engine.safety import require_confirmation, SafetyContext
from engine.laravel_sail import sail_installed, install_sail


# -------------------------------------------------
# Workflow result
# -------------------------------------------------
@dataclass(frozen=True)
class WorkflowResult:
    ok: bool
    steps: list[str]
    result: Optional[CommandResult] = None
    error: Optional[str] = None

    @classmethod
    def success(
        cls,
        *,
        steps: Iterable[str],
        result: Optional[CommandResult] = None,
    ) -> "WorkflowResult":
        return cls(
            ok=True,
            steps=list(steps),
            result=result,
        )

    @classmethod
    def failure(
        cls,
        *,
        steps: Iterable[str],
        error: str,
        result: Optional[CommandResult] = None,
    ) -> "WorkflowResult":
        return cls(
            ok=False,
            steps=list(steps),
            error=error,
            result=result,
        )


# -------------------------------------------------
# Workflows
# -------------------------------------------------
def start_environment(
    project: Path,
    *,
    auto_migrate: bool = True,
    ensure_sail: bool = False,
    wait_for_health: bool = True,
    health_service: str = "mysql",
    health_timeout: int = 60,
) -> WorkflowResult:
    """
    Start the Docker environment and optionally:
    - wait for service health
    - install Laravel Sail if missing
    - run migrations

    Order is important and intentional.
    """
    steps: list[str] = []

    # -------------------------------------------------
    # Docker up
    # -------------------------------------------------
    result = docker_compose_up(project)
    if not result.ok:
        return WorkflowResult.failure(
            steps=steps,
            error="Docker failed to start",
            result=result,
        )

    steps.append("Docker environment started")

    mark_mysql_initialized(project)
    steps.append("MySQL marked as initialized")

    # -------------------------------------------------
    # Optional health check
    # -------------------------------------------------
    if wait_for_health:
        healthy = wait_for_service_healthy(
            project,
            service=health_service,
            timeout=health_timeout,
        )

        if not healthy:
            return WorkflowResult.failure(
                steps=steps,
                error=f"Service '{health_service}' did not become healthy in time",
            )

        steps.append(f"Service '{health_service}' is healthy")

    # -------------------------------------------------
    # Optional Sail install
    # -------------------------------------------------
    if ensure_sail:
        if sail_installed(project):
            steps.append("Laravel Sail already installed")
        else:
            sail = install_sail(project)

            if not sail.ok:
                return WorkflowResult.failure(
                    steps=steps,
                    error="Failed to install Laravel Sail",
                    result=sail,
                )

            steps.append("Laravel Sail installed")

    # -------------------------------------------------
    # Optional migrations
    # -------------------------------------------------
    if auto_migrate:
        mig = artisan(project, ["migrate"])

        if not mig.ok:
            return WorkflowResult.failure(
                steps=steps,
                error="Database migration failed",
                result=mig,
            )

        steps.append("Database migrations completed")

    return WorkflowResult.success(
        steps=steps,
        result=result,
    )


def reset_database(
    project: Path,
    *,
    seed: bool,
    safety: SafetyContext,
) -> WorkflowResult:
    """
    Reset the database using migrate:fresh.
    """
    require_confirmation(
        safety,
        action="reset database (migrate:fresh)",
    )

    steps: list[str] = []

    result = artisan(project, ["migrate:fresh"])

    if not result.ok:
        return WorkflowResult.failure(
            steps=steps,
            error="migrate:fresh failed",
            result=result,
        )

    steps.append("Database reset with migrate:fresh")

    if seed:
        seed_result = artisan(project, ["db:seed"])

        if not seed_result.ok:
            return WorkflowResult.failure(
                steps=steps,
                error="Database seeding failed",
                result=seed_result,
            )

        steps.append("Database seeded")

    return WorkflowResult.success(
        steps=steps,
        result=result,
    )


def stop_environment(
    project: Path,
    *,
    safety: SafetyContext,
) -> WorkflowResult:
    """
    Stop the Docker environment.
    """
    require_confirmation(
        safety,
        action="stop docker environment",
    )

    steps: list[str] = []

    result = docker_compose_down(project)

    if not result.ok:
        return WorkflowResult.failure(
            steps=steps,
            error="Docker down failed",
            result=result,
        )

    steps.append("Docker environment stopped")

    return WorkflowResult.success(
        steps=steps,
        result=result,
    )
