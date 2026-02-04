import sys
import asyncio
import platform


def setup_asyncio():
    """
    Configure asyncio event loop policy for Python 3.13+ (Windows-safe).
    Safe to call multiple times.
    """
    if sys.version_info < (3, 13):
        return

    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(
            asyncio.WindowsSelectorEventLoopPolicy()
        )

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
