from typing import Protocol


class RoundingStrategy(Protocol):
    def allocate_remainder(
        self,
        *,
        remainder_kobo: int,
        gtbank_kobo: int,
        insureflow_kobo: int,
        broker_kobo: int,
        insurer_payable_kobo: int,
    ) -> tuple[int, int, int, int]:
        """Distributes remainder_kobo (the kobo lost to flooring each bps
        share independently) across the four buckets. Must return
        (gtbank_kobo, insureflow_kobo, broker_kobo, insurer_payable_kobo)
        summing to the original four inputs plus remainder_kobo exactly --
        callers assert this, so an implementation that drops or duplicates
        kobo will fail loudly rather than silently leak money.
        """
        ...


class RemainderToInsurerPayableStrategy:
    """Default strategy (PRD §13.1) -- explicitly provisional pending finance
    sign-off, see docs/adr/0001-kobo-rounding.md. Routes 100% of the
    flooring remainder to INSURER_PAYABLE, since GTBank/Insureflow/broker
    rates are contractual bps figures that should never silently drift
    upward by a kobo or two.
    """

    def allocate_remainder(
        self,
        *,
        remainder_kobo: int,
        gtbank_kobo: int,
        insureflow_kobo: int,
        broker_kobo: int,
        insurer_payable_kobo: int,
    ) -> tuple[int, int, int, int]:
        return gtbank_kobo, insureflow_kobo, broker_kobo, insurer_payable_kobo + remainder_kobo


_STRATEGIES: dict[str, RoundingStrategy] = {
    "remainder_to_insurer_payable": RemainderToInsurerPayableStrategy(),
}

DEFAULT_ROUNDING_STRATEGY = "remainder_to_insurer_payable"


def get_rounding_strategy(name: str = DEFAULT_ROUNDING_STRATEGY) -> RoundingStrategy:
    try:
        return _STRATEGIES[name]
    except KeyError:
        raise ValueError(f"unknown rounding strategy: {name}") from None
