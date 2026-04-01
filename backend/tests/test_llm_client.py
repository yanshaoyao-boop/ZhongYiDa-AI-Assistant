import asyncio
import sys
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from services import llm_client  # noqa: E402


def _run_in_fresh_loop(coro_factory):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro_factory())
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()


class LlmClientTestCase(unittest.TestCase):
    def tearDown(self):
        _run_in_fresh_loop(llm_client.close_client)

    def test_get_client_recreates_async_client_for_new_event_loop(self):
        async def capture_client_id():
            client = llm_client.get_client()
            return id(client)

        first_client_id = _run_in_fresh_loop(capture_client_id)
        second_client_id = _run_in_fresh_loop(capture_client_id)

        self.assertNotEqual(first_client_id, second_client_id)


if __name__ == "__main__":
    unittest.main()
