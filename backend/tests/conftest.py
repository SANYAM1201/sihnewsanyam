import os
import sys
import tempfile

os.environ["ULTRALYTICS_AUTOINSTALL"] = "0"
os.environ["YOLO_OFFLINE"] = "1"
os.environ["WATCHDOG_DISABLE"] = "1"

import pytest
from fastapi.testclient import TestClient



@pytest.fixture(autouse=True)
def _reset_db():
    """Use a fresh in-memory SQLite database for each test."""
    from app.config import Settings, get_settings
    from app import database

    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    test_db_url = f"sqlite:///{tmp.name}"

    original_engine = database.engine
    original_SessionLocal = database.SessionLocal

    settings = get_settings()
    old_url = settings.database_url

    database.engine = None
    database.SessionLocal = None
    get_settings.cache_clear()

    os.environ["DATABASE_URL"] = test_db_url
    os.environ["MODEL_PROVIDER"] = "mock"

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.database import Base

    database.engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    database.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=database.engine)
    Base.metadata.create_all(bind=database.engine)

    yield

    database.engine = original_engine
    database.SessionLocal = original_SessionLocal
    os.environ.pop("DATABASE_URL", None)
    os.environ.pop("MODEL_PROVIDER", None)
    if old_url:
        os.environ["DATABASE_URL"] = old_url
    get_settings.cache_clear()

    try:
        os.unlink(tmp.name)
    except OSError:
        pass
