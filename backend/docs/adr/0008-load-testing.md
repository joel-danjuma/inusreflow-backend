# ADR 0008: Load testing the bulk-payment path and the 500-item cap

## Status
Accepted for this build.

## Context
PRD §14 open question #9 left `Settings.max_bulk_payment_items=500` as a configurable-but-unvalidated default. Per the Phase 7 plan, `tests/load/` (Locust) exists to validate that number empirically rather than leave it as an untested guess. No live Squad sandbox credentials are available in this environment (the same caveat already documented in `docs/adr/0005-reconciliation-scope.md`), so `tests/load/run_server.py` serves the real `app.main.app` with `get_squad_client` overridden to `FakeSquadClient` — these numbers measure Insureflow's own request-handling cost (installment validation, one VA-mint round trip, one `PaymentBatch` + N `PaymentBatchItem` insert), not Squad's network latency.

`tests/load/seed_data.py` seeds 5 brokers with 540 due installments each (45 policies × the 12-item rolling installment window in `policy_service.py`), bypassing HTTP and the RLS tenant-context GUC for fast setup (see that file's docstring). `tests/load/locustfile.py` has each simulated broker submit its installment pool as successive 500-item `POST /payments/bulk` batches.

## What the first run found
The first Locust run (`-u 5 -r 5 --run-time 30s` against the seeded data) measured a full 500-item batch at **~8.2s average** (min 8172ms / max 8221ms / median 8200ms across 5 requests), versus ~557ms average for a 40-item tail batch. That gap was disproportionate to item count and pointed at an O(N) cost specific to validation, not the Squad call or the inserts.

The cause: `bulk_payment_service._load_payable_installments` fetched each installment with a separate `db.get()` call in a loop, and for each one called `payment_service.assert_installment_owned_by`, which issued a *second* separate `db.get()` for that installment's policy — roughly **2N sequential DB round trips** (1000, at the 500-item cap) purely to validate existence/status/ownership, before any Squad call or write.

## Decisions

1. **Fixed the N+1 query pattern**, since it was the actual bottleneck the load test exists to surface. `_load_payable_installments` now batch-fetches every installment in one query (`WHERE id IN (...)`) and every referenced policy in a second query, then validates payability/ownership in memory — collapsing validation from 2N round trips to 2, regardless of batch size. Error semantics are unchanged (`NotFoundError` for a missing or not-owned installment, `ConflictError` for a non-payable status), confirmed by the existing `tests/unit/test_bulk_payment_validation.py` suite, which passes unmodified. `payment_service.assert_installment_owned_by` itself is untouched — it's still used as-is by the single-payment path, where N=1 makes the per-call round trip irrelevant.

   Re-measured against freshly seeded data after the fix: a full 500-item batch now averages **~998ms** (min 986ms / max 1004ms / median 1000ms), an ~8x improvement; the 40-item tail batch averages ~194ms (min 145ms / max 232ms). Zero failures across both runs once each batch targeted installments that hadn't already been claimed by a prior run.

2. **`Settings.max_bulk_payment_items` stays at 500, unchanged.** With the N+1 fix, the cap itself was never the bottleneck — a full 500-item batch resolves in about a second, well inside any reasonable client/gateway timeout, and 5 concurrent brokers each submitting a full batch simultaneously showed no meaningful latency degradation against the local Postgres instance. There's no empirical basis here to lower it, and raising it is out of scope for this load test — 500 was a design choice (bounding our own payload/fan-out cost, per CLAUDE.md), not a number this data was meant to challenge upward.

## Caveats
- Single machine, single Postgres container (the same `docker compose` instance the rest of the test suite uses) — not a staging- or production-scale environment. Absolute numbers will shift under real network latency, real Squad calls, and production-grade DB infrastructure; what this validates is the *relative* finding (the cap doesn't matter once the validation loop is fixed), not a pinned production SLA.
- `FakeSquadClient`'s VA-mint call is in-process and effectively instant. A real Squad call adds genuine external network latency on top of these numbers — but that cost is now back to being the dominant, expected cost of the request (an external dependency outside Insureflow's control), not a self-inflicted N+1 query.
- Tested at 5 concurrent simulated brokers, matching this product's 1:1 broker-insurer tenancy shape at modest scale — not validated at materially higher concurrency. Re-run this suite rather than assume these numbers hold if broker volume grows substantially.

## Reproducing
```bash
docker compose up -d
uv run python -m tests.load.seed_data
uv run python -m tests.load.run_server &   # serves on 127.0.0.1:8001, FakeSquadClient
uv run locust -f tests/load/locustfile.py --headless \
    -u 5 -r 5 --run-time 30s --host http://127.0.0.1:8001 \
    --csv tests/load/results/run
```
`tests/load/seed_data.json` and `tests/load/results/` are generated by these commands and are git-ignored, not committed.

## Consequences
- `_load_payable_installments` now contains its own in-memory ownership check (comparing a batch-fetched `Policy`'s `broker_id`/`insurance_company_id`) instead of delegating per-installment to `payment_service.assert_installment_owned_by` — a small, intentional duplication accepted as the cost of collapsing 2N round trips into 2.
- Any future change to ownership-check semantics in `payment_service.assert_installment_owned_by` must be mirrored in `bulk_payment_service._load_payable_installments` (and vice versa) — they are no longer the same code path, only the same logic.
