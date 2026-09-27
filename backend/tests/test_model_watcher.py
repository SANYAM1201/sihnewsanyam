from unittest.mock import MagicMock, patch
from pathlib import Path
import pytest

from app.services.model_watcher import ModelWatcher, _Handler


def test_handler_check():
    handler = _Handler()
    mock_event = MagicMock()
    mock_event.is_directory = False
    mock_event.src_path = "/path/to/test.txt"

    # Non model file should be ignored
    handler.on_modified(mock_event)
    handler.on_created(mock_event)

    # Model file
    mock_event.src_path = "models/best.pt"
    with patch("app.services.model_manager.model_manager.list", return_value={"yolov8s": {"path": "models/best.pt"}}), \
         patch("app.services.model_manager.model_manager.reload") as mock_reload:
        handler.on_modified(mock_event)
        mock_reload.assert_called_with("yolov8s")

        handler.on_created(mock_event)


def test_model_watcher_start_stop(tmp_path: Path):
    watcher = ModelWatcher(str(tmp_path))
    watcher.start()
    assert watcher._obs is not None
    watcher.stop()
