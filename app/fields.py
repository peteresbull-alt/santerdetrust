from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models


def _fernet():
    key = getattr(settings, 'FIELD_ENCRYPTION_KEY', None)
    if not key:
        raise ImproperlyConfigured('FIELD_ENCRYPTION_KEY is not set; it is required to read or save encrypted fields.')
    return Fernet(key)


class EncryptedCharField(models.CharField):
    """
    CharField whose value is encrypted (Fernet, AES-128 + HMAC) in the database
    and decrypted when loaded. Encrypted values cannot be searched or filtered.
    """

    def from_db_value(self, value, expression, connection):
        if not value:
            return value
        try:
            return _fernet().decrypt(value.encode()).decode()
        except InvalidToken:
            # Plain-text value saved before encryption was introduced
            return value

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if not value:
            return value
        return _fernet().encrypt(value.encode()).decode()
