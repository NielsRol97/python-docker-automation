import sys
import asyncio
import platform
from pathlib import Path

# ---- Python 3.13+ asyncio bootstrap (Windows-safe) ----
if sys.version_info >= (3, 13):
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
# ------------------------------------------------------

import streamlit.web.bootstrap as bootstrap

app_path = Path(__file__).parent / "ui.py"

bootstrap.run(
    str(app_path),
    is_hello=False,
    args=[],
    flag_options={},
)
