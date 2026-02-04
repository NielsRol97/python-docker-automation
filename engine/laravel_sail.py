from __future__ import annotations

import json
from pathlib import Path

from engine.artisan import artisan
from engine.docker import CommandResult


def sail_installed(project: Path) -> bool:
    composer = project / "composer.json"
    if not composer.is_file():
        return False

    try:
        data = json.loads(composer.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False

    require = data.get("require-dev", {})
    return "laravel/sail" in require


def install_sail(project: Path) -> CommandResult:
    """
    Install Laravel Sail via Composer and run sail:install.
    Assumes containers are running.
    """
    # 1. Require Sail
    result = artisan(
        project,
        ["require", "laravel/sail", "--dev"],
        timeout=300,
    )
    if not result.ok:
        return result

    # 2. Run Sail installer (no prompt)
    return artisan(
        project,
        ["sail:install", "--no-interaction"],
        timeout=300,
    )
