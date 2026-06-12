"""Small cross-platform helpers."""
from __future__ import annotations

import os
import subprocess
import sys


def open_file(path: str) -> None:
    """Open a file with the OS default application.

    Works on Windows, macOS and Linux. Uses argument lists (never a shell
    string) so paths with spaces or shell metacharacters are handled safely.
    """
    if not path:
        return

    try:
        if sys.platform.startswith("darwin"):
            subprocess.run(["open", path], check=False)
        elif os.name == "nt":
            os.startfile(path)  # type: ignore[attr-defined]  # Windows-only
        else:
            subprocess.run(["xdg-open", path], check=False)
    except Exception as exc:  # pragma: no cover - environment dependent
        print(f"Failed to open file '{path}': {exc}")
