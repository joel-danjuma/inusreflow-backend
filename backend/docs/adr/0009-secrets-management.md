# ADR 0009: Secrets management (deploy-time, not built in this repo)

## Status
Accepted for this build. Provisional in scope: documents the intended deploy-time approach without building it, since no target deploy environment (cloud provider, orchestrator) has been chosen yet.

## Context
`app/core/config.py`'s `Settings` (pydantic-settings) loads every credential — `jwt_secret_key`, `squad_secret_key`/`squad_public_key`, `app_database_url`/`database_url`, `pii_encryption_key` — from environment variables, with `.env` as the local-dev source (git-ignored from Phase 0). Every one of these fields ships an insecure, clearly-labeled placeholder default (e.g. `"local-dev-secret-change-me-please-this-is-not-for-prod"`) so the app boots out of the box locally, but nothing stops those defaults from leaking into a real deploy by omission. CLAUDE.md already states the requirement — "Squad API keys belong in a secrets manager, never in source control or committed env files... sandbox and live credentials must stay strictly separated per environment, never co-loaded" — but no secrets-manager integration exists in code, and building one is premature without a chosen deploy target (AWS/GCP/Azure/bare VPS all imply different native tooling).

## Decision
Defer the actual integration; lock in the contract any future integration must satisfy, so it's a drop-in change rather than a redesign:

1. **`Settings` stays the single source of truth for config**, sourced purely from environment variables (`pydantic-settings`'s existing `env_file`/env-var precedence). A secrets-manager integration's job is only to *populate the process environment before the app starts* (e.g. an entrypoint script that resolves secrets from AWS Secrets Manager / GCP Secret Manager / Vault and exports them, then execs `uvicorn`) — `app/core/config.py` itself never calls out to a secrets API directly. This keeps `Settings` provider-agnostic and keeps tests (which already override `Settings` via env vars/fixtures) unaffected.
2. **Sandbox and live Squad credentials are never co-loaded.** `squad_secret_key`/`squad_public_key`/`squad_base_url`/`squad_merchant_id` are a single set of fields, not sandbox/live pairs — the environment a process runs in (local/staging → sandbox, production → live) determines which real values get resolved into those fields at deploy time. There is no code path that reads both at once, and no future change should add one (a process should never hold both a sandbox and a live Squad secret in memory simultaneously).
3. **Rotation is an environment-variable swap, not a code change.** Because nothing in `app/` reads a secret anywhere except through `get_settings()` (`@lru_cache`d per-process), rotating any credential is restart-the-process-with-new-env, never an in-app code path. (The `@lru_cache` means a running process won't pick up a rotated secret without a restart — acceptable for now since none of these credentials are rotated automatically yet; revisit if a future requirement needs hot rotation without a restart.)
4. **Local dev keeps `.env` + insecure placeholder defaults exactly as-is.** This ADR doesn't change Phase 0's `.env`-for-local-dev setup — it only constrains what a non-local deploy is allowed to do, which is never to rely on these defaults or commit real values anywhere `git` can see them.

## Consequences
- No new code lands from this ADR — `app/core/config.py` already satisfies the contract above (env-var-sourced, no hardcoded secrets, sandbox/live fields never structurally duplicated).
- Whoever picks the deploy target later (cloud provider, k8s vs. plain VM, etc.) implements *only* an entrypoint/init step that resolves secrets into the environment before the app process starts — no `Settings` changes anticipated.
- If a future requirement needs hot rotation without a restart, `get_settings()`'s `@lru_cache` would need to change to a TTL'd or explicitly-invalidated cache — not done now since nothing currently demands it.
