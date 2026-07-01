"""Empirically validates Settings.max_bulk_payment_items=500 (PRD §14
open question #9) by hammering POST /payments/bulk at the cap and measuring
real latency, per docs/adr/0008-load-testing.md.

Usage (after tests.load.seed_data has populated seed_data.json, and
tests.load.run_server is listening on :8001):

    uv run locust -f tests/load/locustfile.py --headless \
        -u 5 -r 5 --run-time 30s --host http://127.0.0.1:8001 \
        --csv tests/load/results

Each seeded broker has a fixed pool of due installments (tests/load/seed_data.py:
POLICIES_PER_BROKER * 12), chunked here into batches of exactly
Settings.max_bulk_payment_items -- once a broker's pool is exhausted that
simulated user stops itself (StopUser) rather than looping forever against
already-paid installments.
"""

import json
import uuid
from itertools import islice
from pathlib import Path
from typing import Any

from locust import HttpUser, between, events, task
from locust.exception import StopUser

MAX_BULK_PAYMENT_ITEMS = 500

_SEED_PATH = Path(__file__).parent / "seed_data.json"
_brokers: list[dict[str, Any]] = []
_next_broker_index = 0


def _chunk(items: list[str], size: int) -> list[list[str]]:
    it = iter(items)
    return [
        chunk for chunk in (list(islice(it, size)) for _ in range(0, len(items), size)) if chunk
    ]


@events.test_start.add_listener
def _load_seed_data(environment: Any, **kwargs: Any) -> None:
    global _brokers
    data = json.loads(_SEED_PATH.read_text())
    _brokers = data["brokers"]


class BulkPaymentUser(HttpUser):
    """One simulated user == one broker submitting its full installment pool
    as successive max-sized bulk batches -- the realistic shape of bulk
    collection (CLAUDE.md: "one debit, one settlement" per action), not a
    sustained-throughput simulation.
    """

    wait_time = between(0.1, 0.5)

    def on_start(self) -> None:
        global _next_broker_index
        if _next_broker_index >= len(_brokers):
            raise StopUser
        broker = _brokers[_next_broker_index]
        _next_broker_index += 1

        self.headers = {"Authorization": f"Bearer {broker['jwt']}"}
        self.chunks = _chunk(broker["installment_ids"], MAX_BULK_PAYMENT_ITEMS)

    @task
    def submit_bulk_payment(self) -> None:
        if not self.chunks:
            raise StopUser
        chunk = self.chunks.pop(0)
        self.client.post(
            "/api/v1/payments/bulk",
            json={"installment_ids": chunk},
            headers={**self.headers, "Idempotency-Key": str(uuid.uuid4())},
            name=f"/api/v1/payments/bulk [{len(chunk)} items]",
        )
