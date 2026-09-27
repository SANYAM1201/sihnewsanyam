import os
import pytest
from app.services.supabase_sync import sync


def test_supabase_sync_loads():
    """SupabaseSync must load without crashing even without credentials."""
    assert sync is not None


def test_supabase_client_inactive_without_creds():
    """Without SUPABASE_URL/KEY env vars the client should be None."""
    if not (os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_KEY")):
        assert sync.client is None, "Expected client=None when no credentials are set"


@pytest.mark.asyncio
async def test_sync_detection_noop_without_creds():
    """sync_detection must not crash when client is None."""
    await sync.sync_detection({"detection_id": "test-001", "class_label": "debris"})


@pytest.mark.asyncio
async def test_sync_all_noop_without_creds():
    """sync_all must not crash when client is None."""
    await sync.sync_all()
