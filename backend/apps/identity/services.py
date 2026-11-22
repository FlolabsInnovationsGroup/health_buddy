"""Public interface of the identity app. Other apps call these functions, not the models."""

import uuid

from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import Subject, SubjectLink, User


class AdultAttestationRequired(Exception):
    """The person did not confirm they are 18 or older."""


class EmailAlreadyRegistered(Exception):
    """An account with this email already exists."""


@transaction.atomic
def register_user(
    *, email: str, password: str, adult_attested: bool, display_name: str = ""
) -> User:
    """Create a user and their pseudonymous subject.

    Raises AdultAttestationRequired, EmailAlreadyRegistered, or
    django.core.exceptions.ValidationError when the password is rejected.
    """
    if adult_attested is not True:
        raise AdultAttestationRequired
    email = email.strip().lower()
    candidate = User(email=email, display_name=display_name)
    validate_password(password, user=candidate)
    try:
        # Savepoint, so a duplicate does not poison the surrounding request transaction.
        with transaction.atomic():
            user = User.objects.create_user(
                email=email,
                password=password,
                display_name=display_name,
                adult_attested_at=timezone.now(),
            )
    except IntegrityError as exc:
        raise EmailAlreadyRegistered from exc
    SubjectLink.objects.create(user=user, subject=Subject.objects.create())
    return user


def get_subject_id_for_user(user: User) -> uuid.UUID:
    """The subject id for a user. Raises SubjectLink.DoesNotExist if there is none."""
    return SubjectLink.objects.values_list("subject_id", flat=True).get(user_id=user.pk)
