from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


# -------------------------------------------------
# Safety policy
# -------------------------------------------------
@dataclass(frozen=True)
class SafetyContext:
    project: Path
    confirmed: bool = False
    force: bool = False  # CLI override


class SafetyError(RuntimeError):
    pass


def require_confirmation(
    ctx: SafetyContext,
    *,
    action: str,
) -> None:
    """
    Enforce confirmation for destructive actions.
    """
    if ctx.force:
        return

    if not ctx.confirmed:
        raise SafetyError(
            f"Action '{action}' requires explicit confirmation"
        )
