import hashlib
import hmac
import json


def compute_dynamic_va_signature(
    *,
    secret_key: str,
    transaction_reference: str,
    amount_received: str,
    merchant_reference: str,
) -> str:
    """HMAC-SHA512, keyed with the merchant secret key, over the
    JSON-serialized object {"transaction_reference", "amount_received",
    "merchant_reference"} in that key order -- see docs/adr/0004 for why
    this is documented-but-not-yet-empirically-confirmed, and why that's
    safe (independent re-query gates every financial state change).
    """
    payload = json.dumps(
        {
            "transaction_reference": transaction_reference,
            "amount_received": amount_received,
            "merchant_reference": merchant_reference,
        },
        separators=(",", ":"),
    )
    return hmac.new(secret_key.encode(), payload.encode(), hashlib.sha512).hexdigest()


def verify_dynamic_va_signature(
    *,
    secret_key: str,
    header_signature: str,
    transaction_reference: str,
    amount_received: str,
    merchant_reference: str,
) -> bool:
    expected = compute_dynamic_va_signature(
        secret_key=secret_key,
        transaction_reference=transaction_reference,
        amount_received=amount_received,
        merchant_reference=merchant_reference,
    )
    return hmac.compare_digest(expected, header_signature.strip().lower())
