import asyncio
import pytest
from unittest.mock import MagicMock, patch

from app.services.supabase_sync import SupabaseSync


@pytest.mark.asyncio
async def test_supabase_sync_unconfigured():
    sync = SupabaseSync()
    sync.client = None
    # None client should safely no-op
    await sync.sync_detection({"id": "1"})
    await sync.sync_run({"id": "1"})
    await sync.sync_all(local_detections=[{"id": "1"}], local_runs=[{"id": "1"}])


@pytest.mark.asyncio
async def test_supabase_sync_configured():
    sync = SupabaseSync()
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_client.table.return_value = mock_table
    sync.client = mock_client

    await sync.sync_detection({"id": "det-1"})
    mock_table.insert.assert_called_with({"id": "det-1"})

    await sync.sync_run({"id": "run-1"})
    mock_table.insert.assert_called_with({"id": "run-1"})

    await sync.sync_all([{"id": "d1"}], [{"id": "r1"}])


@pytest.mark.asyncio
async def test_supabase_sync_errors():
    sync = SupabaseSync()
    mock_client = MagicMock()
    mock_client.table.side_effect = Exception("DB error")
    sync.client = mock_client

    # Should catch and log error without raising
    await sync.sync_detection({"id": "det-1"})
    await sync.sync_run({"id": "run-1"})
