from app.integrations.squad.signature import (
    compute_dynamic_va_signature,
    verify_dynamic_va_signature,
)

_PARAMS = {
    "secret_key": "sk_test_123",
    "transaction_reference": "txn_abc",
    "amount_received": "10000",
    "merchant_reference": "merchant_abc",
}


def test_verify_accepts_matching_signature() -> None:
    signature = compute_dynamic_va_signature(**_PARAMS)
    assert verify_dynamic_va_signature(header_signature=signature, **_PARAMS)


def test_verify_rejects_tampered_amount() -> None:
    signature = compute_dynamic_va_signature(**_PARAMS)
    tampered = {**_PARAMS, "amount_received": "99999"}
    assert not verify_dynamic_va_signature(header_signature=signature, **tampered)


def test_verify_rejects_wrong_secret_key() -> None:
    signature = compute_dynamic_va_signature(**_PARAMS)
    wrong_key = {**_PARAMS, "secret_key": "sk_other_key"}
    assert not verify_dynamic_va_signature(header_signature=signature, **wrong_key)


def test_verify_is_case_insensitive_and_strips_whitespace_on_header() -> None:
    signature = compute_dynamic_va_signature(**_PARAMS)
    assert verify_dynamic_va_signature(header_signature=f" {signature.upper()} ", **_PARAMS)
