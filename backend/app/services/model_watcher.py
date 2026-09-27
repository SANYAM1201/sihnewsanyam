"""Watch models/ directory and auto-reload changed model files."""

from __future__ import annotations

import logging
from pathlib import Path

from app.services.model_manager import model_manager

logger = logging.getLogger(__name__)

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer

    class _Handler(FileSystemEventHandler):
        def _check(self, path: str) -> None:
            p = Path(path)
            if p.suffix not in (".pt", ".pth", ".engine"):
                return
            for name, cfg in model_manager.list().items():
                if Path(cfg["path"]).resolve() == p.resolve():
                    logger.info(f"🔄 File changed: {p.name} — reloading model '{name}'")
                    model_manager.reload(name)

        def on_modified(self, event) -> None:
            if not event.is_directory:
                self._check(event.src_path)

        def on_created(self, event) -> None:
            if not event.is_directory:
                self._check(event.src_path)

    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False
    _Handler = None
    logger.warning("⚠️  watchdog package not installed — model hot-reloading disabled")



class ModelWatcher:
    def __init__(self, watch_dir: str = "models") -> None:
        self._dir = Path(watch_dir)
        self._obs = Observer() if HAS_WATCHDOG else None

    def start(self) -> None:
        import os

        if os.getenv("WATCHDOG_DISABLE") == "1":
            return
        if HAS_WATCHDOG and self._obs and self._dir.exists():
            self._obs.schedule(_Handler(), str(self._dir), recursive=False)
            self._obs.start()
            logger.info(f"👀 Watching {self._dir}/ for model changes")


    def stop(self) -> None:
        if HAS_WATCHDOG and self._obs and self._obs.is_alive():
            self._obs.stop()
            self._obs.join()


watcher = ModelWatcher()
