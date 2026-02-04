from pathlib import Path
from engine.bootstrap import setup_asyncio
import streamlit.web.bootstrap as bootstrap


def main():
    setup_asyncio()

    app_path = Path(__file__).parent / "ui.py"

    bootstrap.run(
        str(app_path),
        is_hello=False,
        args=[],
        flag_options={},
    )


if __name__ == "__main__":
    main()
