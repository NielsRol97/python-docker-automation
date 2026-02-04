from __future__ import annotations

from pathlib import Path
import json
from dotenv import dotenv_values


DOCKER_ENV_DEFAULTS = {
    "DB_HOST": "mysql",
    "DB_PORT": "3306",
    "MAIL_HOST": "mailpit",
    "MAIL_PORT": "1025",
}


def is_laravel_project(path: Path) -> bool:
    artisan = path / "artisan"
    composer = path / "composer.json"

    if not artisan.exists() or not composer.exists():
        return False

    try:
        data = json.loads(composer.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False

    req = data.get("require") or {}
    return "laravel/framework" in req


def list_laravel_projects(projects_root: Path) -> list[Path]:
    """
    Return direct child folders that are Laravel projects.
    """
    candidates = [p for p in projects_root.iterdir() if p.is_dir()]
    projects = [p for p in candidates if is_laravel_project(p)]
    return sorted(projects, key=lambda p: p.name.lower())


def ensure_env_defaults(project_path: Path) -> list[str]:
    """
    Ensure docker-related defaults exist in .env.
    Returns list of keys that were modified or added.
    """
    env_path = project_path / ".env"
    if not env_path.exists():
        return []

    raw_lines = env_path.read_text(encoding="utf-8").splitlines()
    existing = dotenv_values(dotenv_path=env_path)

    desired = {
        **DOCKER_ENV_DEFAULTS,
        "MAIL_MAILER": existing.get("MAIL_MAILER") or "smtp",
        "MAIL_USERNAME": existing.get("MAIL_USERNAME") or "null",
        "MAIL_PASSWORD": existing.get("MAIL_PASSWORD") or "null",
        "MAIL_ENCRYPTION": existing.get("MAIL_ENCRYPTION") or "null",
    }

    changed_keys: list[str] = []
    remaining = set(desired.keys())
    new_lines: list[str] = []

    for line in raw_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            new_lines.append(line)
            continue

        key, _ = line.split("=", 1)
        key = key.strip()

        if key in desired:
            new_line = f"{key}={desired[key]}"
            if line != new_line:
                changed_keys.append(key)
            new_lines.append(new_line)
            remaining.discard(key)
        else:
            new_lines.append(line)

    if remaining:
        new_lines.append("")
        new_lines.append("# --- docker defaults ---")
        for key in sorted(remaining):
            new_lines.append(f"{key}={desired[key]}")
            changed_keys.append(key)

    if changed_keys:
        env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    return changed_keys
