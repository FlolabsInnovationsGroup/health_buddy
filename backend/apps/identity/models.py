"""Identity data: who a person is, and the pseudonymous subject their health data hangs on.

The health apps never reference User. They store a subject_id only. The link between the
two lives in SubjectLink, and nothing outside this app should import it directly.
"""

import uuid

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower
from django.utils import timezone


class UserManager(BaseUserManager):
    use_in_migrations = True

    def get_by_natural_key(self, email):
        # Sign-in is case-insensitive on email.
        return self.get(email__iexact=email)

    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("An email address is required.")
        if not password:
            raise ValueError("A password is required.")
        user = self.model(email=email.strip().lower(), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    """A person who can sign in. Holds contact details only, never health data."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Always stored lowercase; the check constraint below enforces it at the database.
    email = models.EmailField(max_length=254, unique=True)
    display_name = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)
    # We record that the person confirmed they are 18 or older, and when. We do not
    # store a date of birth.
    adult_attested_at = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(email=Lower("email")),
                name="identity_user_email_lowercase",
            ),
        ]

    def __str__(self):
        return str(self.id)


class Subject(models.Model):
    """A pseudonymous identifier for one person's health data. Carries no personal details."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.id)


class SubjectLink(models.Model):
    """The only place a User is tied to a Subject.

    Deleting a user removes this row. The Subject, and any health data pointing at it,
    is then no longer attributable to a person.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="subject_link")
    subject = models.OneToOneField(Subject, on_delete=models.PROTECT, related_name="link")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user_id} -> {self.subject_id}"
