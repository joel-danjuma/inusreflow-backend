from prometheus_client import Counter

#: One counter per financial/security surface introduced in Phases 4-7,
#: not a general sweep of every code path -- these are the outcomes an
#: operator actually needs to alert on (PRD §11.5/§14's observability ask).
payment_outcomes_total = Counter(
    "insureflow_payment_outcomes_total",
    "Single payments resolved to a terminal status",
    ["status"],
)
payment_batch_outcomes_total = Counter(
    "insureflow_payment_batch_outcomes_total",
    "Bulk payment batches resolved to a terminal status",
    ["status"],
)
webhook_events_total = Counter(
    "insureflow_webhook_events_total",
    "Squad webhook deliveries received, by signature validity and outcome",
    ["signature_valid", "processing_status"],
)
settlement_payout_outcomes_total = Counter(
    "insureflow_settlement_payout_outcomes_total",
    "Settlement payout attempts resolved to a terminal or pending status",
    ["status"],
)
rate_limit_rejections_total = Counter(
    "insureflow_rate_limit_rejections_total",
    "Requests rejected by the payment rate limiter, by scope",
    ["scope"],
)
anomaly_flags_total = Counter(
    "insureflow_anomaly_flags_total",
    "Bulk payment batches flagged as anomalous vs. the broker's own trailing history",
)
