from pathlib import Path
from datetime import datetime
import tempfile


class MountError(RuntimeError):
    """Raised when an unexpected file/directory is encountered."""
    pass


def safe_backup(path: Path) -> Path:
    """
    Create a timestamped backup next to the file.
    Example: docker-compose.yml.bak-20260202-223012
    """
    if not path.exists():
        raise FileNotFoundError(f"Cannot backup missing file: {path}")

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = path.with_name(f"{path.name}.bak-{ts}")
    backup.write_bytes(path.read_bytes())
    return backup


def ensure_file(path: Path, content: str = "") -> None:
    """
    Ensure a file exists.
    - Creates parent directories if needed
    - Creates the file if missing (with provided content)
    - Raises if path exists but is a directory
    """
    if path.exists() and path.is_dir():
        raise MountError(f"Expected file but found directory: {path}")

    path.parent.mkdir(parents=True, exist_ok=True)

    if not path.exists():
        _atomic_write(path, content)


def ensure_directory(path: Path) -> None:
    """
    Ensure a directory exists.
    - Raises if path exists but is a file
    """
    if path.exists() and path.is_file():
        raise MountError(f"Expected directory but found file: {path}")

    path.mkdir(parents=True, exist_ok=True)


def _atomic_write(path: Path, content: str) -> None:
    """
    Write file content atomically to avoid partial writes.
    """
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        delete=False,
        dir=str(path.parent),
    ) as tmp:
        tmp.write(content)
        tmp.flush()

    Path(tmp.name).replace(path)
