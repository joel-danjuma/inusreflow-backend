import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.models.commission_config import CommissionConfig
from app.services.commission_service import calculate_split


def _config(
    gtbank_rate_bps: int, insureflow_rate_bps: int, broker_rate_bps: int | None
) -> CommissionConfig:
    return CommissionConfig(
        scope="global",
        gtbank_rate_bps=gtbank_rate_bps,
        insureflow_rate_bps=insureflow_rate_bps,
        broker_rate_bps=broker_rate_bps,
    )


@given(
    gross_amount_kobo=st.integers(min_value=1, max_value=1_000_000_000),
    gtbank_rate_bps=st.integers(min_value=0, max_value=300),
    insureflow_rate_bps=st.integers(min_value=0, max_value=300),
    broker_rate_bps=st.one_of(st.none(), st.integers(min_value=0, max_value=5_000)),
)
@settings(max_examples=500)
def test_split_sums_exactly_to_gross_with_zero_drift(
    gross_amount_kobo: int,
    gtbank_rate_bps: int,
    insureflow_rate_bps: int,
    broker_rate_bps: int | None,
) -> None:
    config = _config(gtbank_rate_bps, insureflow_rate_bps, broker_rate_bps)
    split = calculate_split(gross_amount_kobo, config)

    assert (
        split.gtbank_kobo + split.insureflow_kobo + split.broker_kobo + split.insurer_payable_kobo
        == gross_amount_kobo
    )
    assert split.gtbank_kobo >= 0
    assert split.insureflow_kobo >= 0
    assert split.broker_kobo >= 0
    assert split.insurer_payable_kobo >= 0


@pytest.mark.parametrize("gross_amount_kobo", [1, 2, 3, 7, 99, 101, 9_999])
def test_split_handles_adversarial_tiny_amounts(gross_amount_kobo: int) -> None:
    config = _config(gtbank_rate_bps=50, insureflow_rate_bps=50, broker_rate_bps=200)
    split = calculate_split(gross_amount_kobo, config)

    assert (
        split.gtbank_kobo + split.insureflow_kobo + split.broker_kobo + split.insurer_payable_kobo
        == gross_amount_kobo
    )


def test_default_strategy_routes_floor_remainder_to_insurer_payable() -> None:
    # 1 kobo at 1bps each floors gtbank/insureflow/broker to 0; the insurer
    # gets the entire kobo, per the PRD §13.1 provisional default.
    config = _config(gtbank_rate_bps=1, insureflow_rate_bps=1, broker_rate_bps=None)
    split = calculate_split(1, config)

    assert split.gtbank_kobo == 0
    assert split.insureflow_kobo == 0
    assert split.broker_kobo == 0
    assert split.insurer_payable_kobo == 1


def test_confirmed_default_rates_split_a_typical_premium() -> None:
    # PRD-confirmed defaults: GTBank 0.5%, Insureflow 0.5%, no broker cut.
    config = _config(gtbank_rate_bps=50, insureflow_rate_bps=50, broker_rate_bps=None)
    split = calculate_split(100_000, config)

    assert split.gtbank_kobo == 500
    assert split.insureflow_kobo == 500
    assert split.broker_kobo == 0
    assert split.insurer_payable_kobo == 99_000


def test_rates_summing_above_100_percent_are_rejected() -> None:
    config = _config(gtbank_rate_bps=6_000, insureflow_rate_bps=6_000, broker_rate_bps=None)
    with pytest.raises(ValueError, match="must be within"):
        calculate_split(1_000, config)
