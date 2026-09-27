from unittest.mock import MagicMock, patch
import pytest

from app.services.supabase_service import SupabaseService


def test_supabase_service_unconfigured():
    with patch("app.services.supabase_service.HAS_SUPABASE_SDK", False):
        svc = SupabaseService()
        assert svc.is_configured is False
        assert svc.upload_file("bucket", "path", b"bytes") is None
        assert svc.insert_run({"id": "1"}) is None
        assert svc.insert_detections([{"id": "1"}]) is None
        assert svc.insert_report({"id": "1"}) is None
        assert svc.get_all_runs() == []
        assert svc.get_all_reports() == []


def test_supabase_service_configured():
    mock_client = MagicMock()
    # Mock storage
    mock_bucket = MagicMock()
    mock_bucket.upload.return_value = {"Key": "test"}
    mock_bucket.get_public_url.return_value = "https://supabase.co/test.jpg"
    mock_client.storage.from_.return_value = mock_bucket

    # Mock table operations
    mock_table = MagicMock()
    mock_query = MagicMock()
    mock_query.execute.return_value = MagicMock(data=[{"id": "run-1"}])
    mock_table.insert.return_value = mock_query
    mock_table.select.return_value = mock_table
    mock_table.order.return_value = mock_query
    mock_client.table.return_value = mock_table

    with patch("app.services.supabase_service.HAS_SUPABASE_SDK", True):
        svc = SupabaseService()
        svc.client = mock_client

        assert svc.is_configured is True
        assert svc.upload_file("bucket", "path", b"bytes") == "https://supabase.co/test.jpg"
        assert svc.insert_run({"id": "run-1"}) == {"id": "run-1"}
        assert svc.insert_detections([{"id": "det-1"}]) == [{"id": "run-1"}]
        assert svc.insert_report({"id": "rep-1"}) == {"id": "run-1"}
        assert svc.get_all_runs() == [{"id": "run-1"}]
        assert svc.get_all_reports() == [{"id": "run-1"}]


def test_supabase_service_errors():
    mock_client = MagicMock()
    # Storage upload exception
    mock_bucket = MagicMock()
    mock_bucket.upload.side_effect = Exception("Storage error")
    mock_client.storage.from_.return_value = mock_bucket

    # Table exception
    mock_table = MagicMock()
    mock_table.insert.side_effect = Exception("DB error")
    mock_table.select.side_effect = Exception("DB query error")
    mock_client.table.return_value = mock_table

    svc = SupabaseService()
    svc.client = mock_client

    assert svc.upload_file("b", "p", b"data") is None
    assert svc.insert_run({"id": "1"}) is None
    assert svc.insert_detections([{"id": "1"}]) is None
    assert svc.insert_report({"id": "1"}) is None
    assert svc.get_all_runs() == []
    assert svc.get_all_reports() == []
