from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "local"
    log_level: str = "INFO"

    database_url: str = "postgresql+asyncpg://insureflow:insureflow@localhost:5432/insureflow"
    #: Deliberately a different, non-superuser Postgres role than database_url
    #: (insureflow, the docker-compose bootstrap superuser, which Alembic
    #: still connects as to manage roles/RLS policies/schema). A superuser
    #: always bypasses row-level security regardless of policy, so RLS as
    #: real defense-in-depth (docs/adr/0006-row-level-security.md) requires
    #: the app's runtime queries to go through a role that can't bypass it.
    app_database_url: str = "postgresql+asyncpg://insureflow_app:insureflow_app_local_dev_only@localhost:5432/insureflow"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret_key: str = "local-dev-secret-change-me-please-this-is-not-for-prod"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    squad_secret_key: str = ""
    squad_public_key: str = ""
    squad_base_url: str = "https://sandbox-api-d.squadco.com"
    squad_merchant_id: str = ""
    #: Insureflow's registered GTBank account number; sent as beneficiary_account
    #: when creating a Business SVA for a broker. Must be set in production.
    squad_beneficiary_account: str = ""
    max_bulk_payment_items: int = 500
    #: Byte cap on an uploaded bulk-pay Excel file
    #: (bulk_payment_upload_service.py) -- guards against unbounded parse
    #: cost, independent of max_bulk_payment_items (which caps row count).
    max_bulk_upload_file_bytes: int = 5_000_000

    reconciliation_stale_after_minutes: int = 30
    reconciliation_transfer_list_page_size: int = 50

    #: Days past due_date before an overdue installment becomes "actionable"
    #: on insurer-facing surfaces (Payment Reminders / Outstanding Policies /
    #: POST /reminders/bulk) -- PremiumInstallment.status still flips to
    #: 'overdue' immediately (installment_service.flag_overdue_installments),
    #: this only gates what counts as worth nagging a broker/customer about.
    overdue_grace_period_days: int = 30

    #: Per-broker and per-IP fixed-window limits on payment-initiating
    #: endpoints (PRD §11.5). Deliberately generous defaults -- this guards
    #: against runaway/abusive automation, not normal bulk broker workflows.
    payment_rate_limit_per_broker_per_minute: int = 60
    payment_rate_limit_per_ip_per_minute: int = 120

    #: Per-email and per-IP fixed-window limits on POST /auth/login, added
    #: alongside the OTP onboarding flow -- a 6-digit OTP is far more
    #: brute-forceable than a real password.
    login_rate_limit_per_email_per_minute: int = 5
    login_rate_limit_per_ip_per_minute: int = 20

    #: Anomaly flagging thresholds for a bulk batch vs. the broker's own
    #: trailing history (PRD §11.5) -- flags for human review, never blocks.
    anomaly_batch_item_count_multiplier: float = 5.0
    anomaly_batch_amount_multiplier: float = 5.0
    anomaly_min_history_batches: int = 3

    #: pgcrypto symmetric key for column-level PII/bank-detail encryption
    #: (docs/adr/0007-pii-encryption.md). Local-dev default only -- a real
    #: deploy must override via a secrets manager, never source control.
    pii_encryption_key: str = "local-dev-pii-key-change-me-please-this-is-not-for-prod"


@lru_cache
def get_settings() -> Settings:
    return Settings()
