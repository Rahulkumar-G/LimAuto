import asyncio
import json
from queue import SimpleQueue
from typing import Any, Dict

import aiohttp

from ..utils.logger import get_logger

# Global queue used as a simple UI bus for status updates
status_updates: "SimpleQueue[Dict[str, Any]]" = SimpleQueue()


class MonitoringAgent:
    """Poll an orchestration server and emit status updates."""

    def __init__(self, status_url: str, poll_interval: int = 5) -> None:
        self.status_url = status_url
        self.poll_interval = poll_interval
        self.logger = get_logger(__name__)
        self._task: asyncio.Task | None = None

    async def _poll_once(self, session: aiohttp.ClientSession) -> None:
        try:
            async with session.get(self.status_url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    payload = {
                        "current_agent": data.get("current_agent", ""),
                        "next_agent": data.get("next_agent", ""),
                        "progress_percent": float(data.get("progress_percent", 0.0)),
                    }
                    status_updates.put(payload)
                else:
                    self.logger.warning(
                        f"Status request failed with code {resp.status}"
                    )
        except Exception as e:  # pragma: no cover - network errors
            self.logger.error(f"Failed to fetch status: {e}")

    async def _run(self) -> None:
        async with aiohttp.ClientSession() as session:
            while True:
                await self._poll_once(session)
                await asyncio.sleep(self.poll_interval)

    def start(self) -> None:
        """Start the background polling task."""
        if not self._task:
            self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        """Stop the background task."""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
