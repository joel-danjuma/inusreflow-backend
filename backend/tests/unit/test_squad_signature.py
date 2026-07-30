from app.integrations.squad.signature import (
    compute_static_va_signature,
    verify_static_va_signature,
)

_PARAMS = {
    "secret_key": "sk_test_123",
    "transaction_reference": "txn_abc",
    "virtual_account_number": "0000012345",
    "currency": "NGN",
    "principal_amount": "10000",
    "settled_amount": "10000",
    "customer_identifier": "broker-uuid-789",
}


def test_verify_accepts_matching_signature() -> None:
    signature = compute_static_va_signature(**_PARAMS)
    assert verify_static_va_signature(header_signature=signature, **_PARAMS)


def test_verify_rejects_tampered_principal_amount() -> None:
    signature = compute_static_va_signature(**_PARAMS)
    tampered = {**_PARAMS, "principal_amount": "99999"}
    assert not verify_static_va_signature(header_signature=signature, **tampered)


def test_verify_rejects_wrong_secret_key() -> None:
    signature = compute_static_va_signature(**_PARAMS)
    wrong_key = {**_PARAMS, "secret_key": "sk_other_key"}
    assert not verify_static_va_signature(header_signature=signature, **wrong_key)


def test_verify_rejects_tampered_virtual_account_number() -> None:
    signature = compute_static_va_signature(**_PARAMS)
    tampered = {**_PARAMS, "virtual_account_number": "9999999999"}
    assert not verify_static_va_signature(header_signature=signature, **tampered)


def test_verify_is_case_insensitive_and_strips_whitespace_on_header() -> None:
    signature = compute_static_va_signature(**_PARAMS)
    assert verify_static_va_signature(header_signature=f" {signature.upper()} ", **_PARAMS)
