import hashlib
import hmac


def compute_static_va_signature(
    *,
    secret_key: str,
    transaction_reference: str,
    virtual_account_number: str,
    currency: str,
    principal_amount: str,
    settled_amount: str,
    customer_identifier: str,
) -> str:
    """HMAC-SHA512, keyed with the merchant secret key, over the pipe-delimited
    string of SVA webhook fields. Header sent by Squad: x-squad-signature.
    Fields are used as raw strings from the webhook payload (no parsing).
    """
    payload = "|".join(
        [
            transaction_reference,
            virtual_account_number,
            currency,
            principal_amount,
            settled_amount,
            customer_identifier,
        ]
    )
    return hmac.new(secret_key.encode(), payload.encode(), hashlib.sha512).hexdigest()


def verify_static_va_signature(
    *,
    secret_key: str,
    header_signature: str,
    transaction_reference: str,
    virtual_account_number: str,
    currency: str,
    principal_amount: str,
    settled_amount: str,
    customer_identifier: str,
) -> bool:
    expected = compute_static_va_signature(
        secret_key=secret_key,
        transaction_reference=transaction_reference,
        virtual_account_number=virtual_account_number,
        currency=currency,
        principal_amount=principal_amount,
        settled_amount=settled_amount,
        customer_identifier=customer_identifier,
    )
    return hmac.compare_digest(expected, header_signature.strip().lower())
