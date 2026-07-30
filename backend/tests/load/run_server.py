"""Serves app.main.app for the Locust run (tests/load/locustfile.py), with
get_squad_client overridden to a FakeSquadClient -- no live Squad sandbox
credentials were available to verify request shapes under load (same
caveat as docs/adr/0005-reconciliation-scope.md), and POST /payments/bulk's
own latency (installment validation, one VA mint, one PaymentBatch + N
PaymentBatchItem rows) is what's under test, not Squad's network latency.

Run with `uv run python -m tests.load.run_server` after tests.load.seed_data.
"""

import uvicorn

from app.core.deps import get_squad_client
from app.main import app
from tests.fakes import FakeSquadClient

app.dependency_overrides[get_squad_client] = lambda: FakeSquadClient()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="warning")
