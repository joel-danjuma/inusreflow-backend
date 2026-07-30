from httpx import AsyncClient


async def test_metrics_endpoint_exposes_prometheus_format(client: AsyncClient) -> None:
    """GET /metrics needs no auth (the Prometheus scraper carries no app JWT,
    app/main.py) and must expose the custom counters in exposition format so
    a scrape config pointed at this path actually finds them.
    """
    response = await client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")

    body = response.text
    for metric_name in (
        "insureflow_payment_outcomes_total",
        "insureflow_payment_batch_outcomes_total",
        "insureflow_webhook_events_total",
        "insureflow_settlement_payout_outcomes_total",
        "insureflow_rate_limit_rejections_total",
        "insureflow_anomaly_flags_total",
    ):
        assert metric_name in body
