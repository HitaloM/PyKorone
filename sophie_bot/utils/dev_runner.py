"""Development runner with hot-reload support using watchfiles."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from sophie_bot.utils.logger import log

if TYPE_CHECKING:
    from watchfiles import Change


def run_with_reload(mode: Literal["bot", "scheduler"]) -> None:
    """
    Run the specified mode with hot-reload using watchfiles.

    This function watches the sophie_bot directory for changes and restarts
    the process when files are modified.

    Args:
        mode: The mode to run ('bot' or 'scheduler')
    """
    try:
        from watchfiles import run_process
    except ImportError:
        log.error("watchfiles is not installed. Install it with: uv sync --group dev")
        sys.exit(1)

    project_root = Path(__file__).parent.parent.parent
    watch_dirs = [str(project_root / "sophie_bot")]

    log.info(f"Starting {mode} mode with hot-reload enabled...")
    log.info(f"Watching directories: {watch_dirs}")

    def target() -> None:
        """Target function to run the mode."""
        import os

        os.environ["DEV_RELOAD"] = "false"  # Prevent recursive reload
        os.environ["MODE"] = mode

        if mode == "bot":
            from sophie_bot.modes.bot import start_bot_mode

            start_bot_mode()
        elif mode == "scheduler":
            from sophie_bot.modes.scheduler import start_scheduler_mode

            start_scheduler_mode()

    # Use subprocess approach for cleaner restarts
    try:
        run_process(
            *watch_dirs,
            target=_run_mode_subprocess,
            args=(mode,),
            watch_filter=_python_filter,
        )
    except KeyboardInterrupt:
        pass


def _python_filter(change: "Change", path: str) -> bool:
    """Filter to only watch Python files."""
    return path.endswith(".py")


def _run_mode_subprocess(mode: str) -> None:
    """Run the mode in a subprocess."""
    import os

    env = os.environ.copy()
    env["DEV_RELOAD"] = "false"
    env["MODE"] = mode

    try:
        subprocess.run(
            [sys.executable, "-m", "sophie_bot"],
            env=env,
            cwd=Path(__file__).parent.parent.parent,
        )
    except KeyboardInterrupt:
        log.error("Process interrupted")
