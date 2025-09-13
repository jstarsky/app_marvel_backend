from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class MaxLengthValidator:
    """Validate that the password is not longer than max_length."""

    def __init__(self, max_length=8):
        self.max_length = int(max_length)

    def validate(self, password, user=None):
        if password is None:
            return
        if len(password) > self.max_length:
            raise ValidationError(
                _(f"This password is too long. It must contain at most {self.max_length} characters."),
                code='password_too_long',
            )

    def get_help_text(self):
        return _(f"Your password must contain at most {self.max_length} characters.")
