from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from engine.workflows import (
    start_environment,
    stop_environment,
    reset_database,
    WorkflowResult,
)


@dataclass(frozen=True)
class Preset:
    name: str
    description: str
    run: Callable[..., WorkflowResult]


PRESETS: dict[str, Preset] = {
    "ready": Preset(
        name="Ready for work",
        description="Start Docker + migrate if needed",
        run=lambda project, safety: start_environment(
            project,
            auto_migrate=True,
        ),
    ),
    "fresh": Preset(
        name="Fresh start",
        description="Reset DB, then start environment",
        run=lambda project, safety: (
            reset_database(project, seed=True)
            if reset_database(project, seed=True).ok
            else reset_database(project, seed=True)
        ),
    ),
    "stop": Preset(
        name="Stop environment",
        description="Stop Docker containers",
        run=lambda project, safety: stop_environment(
            project,
            safety=safety,
        ),
    ),
}
