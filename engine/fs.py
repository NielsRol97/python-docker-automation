from pathlib import Path
from datetime import datetime


class MountError(RuntimeError):
    pass


def safe_backup(path: Path) -> Path:
    """
    Create a timestamped backup next to the file.
    Example: docker-compose.yml.bak-20260202-223012
    """
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = path.with_name(f"{path.name}.bak-{ts}")
    backup.write_bytes(path.read_bytes())
    return backup


def ensure_file(path: Path, content: str = "") -> None:
    """
    Ensure a file exists.
    - Creates parent directories if needed
    - Creates the file if missing
    - Raises if path exists but is a directory
    """
    if path.exists() and path.is_dir():
        raise MountError(f"Expected file but found directory: {path}")

    path.parent.mkdir(parents=True, exist_ok=True)

    if not path.exists():
        path.write_text(content, encoding="utf-8")


def ensure_directory(path: Path) -> None:
    """
    Ensure a directory exists.
    - Raises if path exists but is a file
    """
    if path.exists() and path.is_file():
        raise MountError(f"Expected directory but found file: {path}")

    path.mkdir(parents=True, exist_ok=True)
