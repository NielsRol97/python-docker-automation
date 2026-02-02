import time
import subprocess
from pathlib import Path


def wait_for_mysql(project_path: Path, timeout: int = 60) -> bool:
    """
    Wait until MySQL container reports healthy.
    """
    start = time.time()

    while time.time() - start < timeout:
        result = subprocess.run(
            [
                "docker",
                "inspect",
                "--format",
                "{{.State.Health.Status}}",
                f"{project_path.name}-mysql",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            status = result.stdout.strip()
            if status == "healthy":
                return True

        time.sleep(3)

    return False
