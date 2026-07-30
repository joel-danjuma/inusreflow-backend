# ADR 0002: Postgres Row-Level Security deferred

## Status
Accepted — deferred to a pre-go-live hardening phase, not MVP-blocking.

## Context
PRD §11.2 recommends Postgres RLS as defense-in-depth for tenant isolation, on top of application-layer `insurance_company_id` scoping. It's explicitly flagged as recommended hardening, not a launch requirement.

## Decision
MVP relies solely on application-layer tenant scoping via `TenantScopedRepository` (every query filtered by `insurance_company_id`, resolved server-side from JWT claims, never from a request param). RLS policies are added later as an additive migration, belt-and-suspenders alongside the app-layer scoping — not a replacement for it.

## Consequences
- A bug in application-layer scoping could leak cross-tenant data until RLS lands. Multi-tenancy/RBAC tests (`tests/security/test_tenant_isolation.py`) are the primary safeguard until then.
- Revisit before go-live, per PRD §11.2.
