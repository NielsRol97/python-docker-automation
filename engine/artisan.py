from pathlib import Path
import subprocess


def artisan(project: Path, args: list[str]) -> tuple[bool, str]:
    """
    Run a Laravel artisan command inside the app container.
    """
    cmd = [
        "docker",
        "compose",
        "exec",
        "-T",  # no TTY (important for Streamlit)
        "app",
        "php",
        "artisan",
        *args,
    ]

    p = subprocess.run(
        cmd,
        cwd=project,
        capture_output=True,
        text=True,
    )

    out = (p.stdout or "") + ("\n" + p.stderr if p.stderr else "")
    return p.returncode == 0, out.strip()
