from __future__ import annotations
from pathlib import Path
import json
from dotenv import dotenv_values


def is_laravel_project(path: Path) -> bool:
    artisan = path / "artisan"
    composer = path / "composer.json"
    if not artisan.exists() or not composer.exists():
        return False

    try:
        data = json.loads(composer.read_text(encoding="utf-8"))
        req = data.get("require", {}) or {}
        return "laravel/framework" in req
    except Exception:
        return False


def list_laravel_projects(projects_root: Path) -> list[Path]:
    # Only direct subfolders (keeps UI sane)
    candidates = [p for p in projects_root.iterdir() if p.is_dir()]
    return sorted([p for p in candidates if is_laravel_project(p)], key=lambda p: p.name.lower())


def ensure_env_defaults(project_path: Path) -> bool:
    """
    Update .env with docker service hostnames and Mailpit.
    Returns True if changes were written.
    """
    env_path = project_path / ".env"
    if not env_path.exists():
        return False

    raw = env_path.read_text(encoding="utf-8").splitlines()
    existing = dotenv_values(dotenv_path=env_path)

    desired = {
        "DB_HOST": "mysql",
        "DB_PORT": "3306",
        "MAIL_MAILER": existing.get("MAIL_MAILER") or "smtp",
        "MAIL_HOST": "mailpit",
        "MAIL_PORT": "1025",
        "MAIL_USERNAME": existing.get("MAIL_USERNAME") or "null",
        "MAIL_PASSWORD": existing.get("MAIL_PASSWORD") or "null",
        "MAIL_ENCRYPTION": existing.get("MAIL_ENCRYPTION") or "null",
    }

    # Apply edits line-wise (preserve comments/ordering where possible)
    changed = False
    keys = set(desired.keys())
    new_lines = []

    for line in raw:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            new_lines.append(line)
            continue

        k, _v = line.split("=", 1)
        k = k.strip()

        if k in desired:
            new_val = str(desired[k])
            new_line = f"{k}={new_val}"
            if line != new_line:
                changed = True
            new_lines.append(new_line)
            keys.discard(k)
        else:
            new_lines.append(line)

    # Append any missing keys at the end
    if keys:
        changed = True
        new_lines.append("")
        new_lines.append("# --- docker defaults ---")
        for k in sorted(keys):
            new_lines.append(f"{k}={desired[k]}")

    if changed:
        env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    return changed
