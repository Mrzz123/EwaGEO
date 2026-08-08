#!/usr/bin/env python3
import os
import sys

if __name__ == "__main__":
    if "--scheduler-action" in sys.argv:
        action_index = sys.argv.index("--scheduler-action")
        action = sys.argv[action_index + 1] if action_index + 1 < len(sys.argv) else ""
        interval = 10
        if "--scheduler-interval" in sys.argv:
            interval_index = sys.argv.index("--scheduler-interval")
            try:
                interval = int(sys.argv[interval_index + 1])
            except (IndexError, ValueError):
                sys.exit(2)
        if not 5 <= interval <= 720:
            sys.exit(2)
        from liewa.liewa_gui.scheduler import Schtasks

        scheduler = Schtasks()
        actions = {
            "create": lambda: scheduler.create_scheduler(
                elevate=False, interval_minutes=interval
            ),
            "delete": lambda: scheduler.delete_scheduler(elevate=False),
            "run": lambda: scheduler.reload_scheduler(elevate=False),
        }
        if action not in actions:
            sys.exit(2)
        _, succeeded = actions[action]()
        sys.exit(0 if succeeded else 1)
    elif "--run-cli" in sys.argv:
        sys.argv.remove("--run-cli")
        # PyInstaller windowed applications expose stdout/stderr as None.
        # The downloader uses print() for progress, so provide safe streams.
        if sys.stdout is None:
            sys.stdout = open(os.devnull, "w", encoding="utf-8")
        if sys.stderr is None:
            sys.stderr = open(os.devnull, "w", encoding="utf-8")
        from liewa.liewa_cli.main import execute
        execute()
    else:
        from liewa.liewa_gui.main import startup
        startup()
