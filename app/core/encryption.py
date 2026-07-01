from sqlalchemy import LargeBinary, Text, func, type_coerce
from sqlalchemy.sql.elements import BindParameter, ColumnElement
from sqlalchemy.types import TypeDecorator

from app.core.config import get_settings


class EncryptedString(TypeDecorator[str]):
    """Column-level encryption at rest for PII/bank-detail fields, via
    Postgres's pgcrypto extension (docs/adr/0007-pii-encryption.md).

    Encryption/decryption happens in the database via SQL-level
    bind_expression/column_expression, not in Python -- every existing
    query (db.get, select(), ORM attribute access) transparently sees
    plaintext, while the underlying column stores pgp_sym_encrypt's bytea
    ciphertext. type_coerce on the bind side is a Python-only type hint (no
    SQL CAST emitted) telling SQLAlchemy to send the parameter as text, not
    as whatever the bytea-typed impl would otherwise imply.
    """

    impl = LargeBinary
    cache_ok = True

    def bind_expression(self, bindvalue: BindParameter[str]) -> ColumnElement[str]:
        return func.pgp_sym_encrypt(
            type_coerce(bindvalue, Text()), get_settings().pii_encryption_key
        )

    def column_expression(self, col: ColumnElement[str]) -> ColumnElement[str]:
        return func.pgp_sym_decrypt(col, get_settings().pii_encryption_key, type_=Text())
