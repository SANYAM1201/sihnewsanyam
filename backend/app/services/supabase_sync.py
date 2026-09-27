"""Supabase Cloud Synchronization Service for Runs and Detections."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class SupabaseSync:
    def __init__(self) -> None:
        self.client: Optional[Any] = None
        try:
            from app.config import get_settings

            settings = get_settings()
            if getattr(settings, "use_supabase", False) and settings.SUPABASE_URL and settings.SUPABASE_KEY:
                from supabase import create_client

                self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
                logger.info("✅ Supabase client initialized successfully")
        except Exception as e:
            logger.warning(f"⚠️  Supabase init skipped: {e}")

    async def sync_detection(self, data: dict[str, Any]) -> None:
        if not self.client:
            return
        try:
            self.client.table("detections").insert(data).execute()
        except Exception as e:
            logger.error(f"Supabase detection sync error: {e}")

    async def sync_run(self, data: dict[str, Any]) -> None:
        if not self.client:
            return
        try:
            self.client.table("runs").insert(data).execute()
        except Exception as e:
            logger.error(f"Supabase run sync error: {e}")

    async def sync_all(
        self, local_detections: Optional[list[dict[str, Any]]] = None, local_runs: Optional[list[dict[str, Any]]] = None
    ) -> None:
        for d in local_detections or []:
            await self.sync_detection(d)
        for r in local_runs or []:
            await self.sync_run(r)

    async def start_periodic_sync(self, interval: int = 300) -> None:
        while True:
            await self.sync_all()
            await asyncio.sleep(interval)


sync = SupabaseSync()
