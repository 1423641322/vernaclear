from __future__ import annotations

import os
import subprocess
import sys
import traceback
from pathlib import Path


def main() -> int:
    root = Path(sys.executable).resolve().parent
    python = root / "runtime" / "pythonw.exe"
    script = root / "app" / "run.py"
    environment = os.environ.copy()
    environment.update(
        {
            "VERNACLEAR_PORTABLE_ROOT": str(root),
            "PYTHONNOUSERSITE": "1",
            "PYTHONUTF8": "1",
        }
    )
    try:
        subprocess.Popen(
            [str(python), str(script), *sys.argv[1:]],
            cwd=root,
            env=environment,
            close_fds=True,
        )
        return 0
    except Exception:
        logs = root / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        (logs / "startup-error.log").write_text(traceback.format_exc(), encoding="utf-8")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
