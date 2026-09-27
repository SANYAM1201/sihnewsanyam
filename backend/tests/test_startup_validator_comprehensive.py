import sys
import pytest
from unittest.mock import patch, MagicMock

from app.services.startup_validator import validate_environment, validate_config


def test_validate_environment_success():
    # Calling validate_environment under normal test conditions
    validate_environment()


def test_validate_environment_missing_module():
    with patch("importlib.import_module", side_effect=ImportError("mocked error")):
        # Under pytest, does not hard sys.exit
        validate_environment()


def test_validate_config_basic():
    validate_config()


def test_validate_config_supabase_missing():
    mock_settings = MagicMock()
    mock_settings.use_supabase = True
    mock_settings.SUPABASE_URL = None
    mock_settings.SUPABASE_KEY = None

    with patch("app.config.get_settings", return_value=mock_settings):
        validate_config()
