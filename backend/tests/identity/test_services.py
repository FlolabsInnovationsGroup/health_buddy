import uuid

import pytest
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from apps.identity import services
from apps.identity.models import Subject, SubjectLink, User

PASSWORD = "a-long-test-passphrase-42"

pytestmark = pytest.mark.django_db


def make_user(email="ada@example.com"):
    return services.register_user(email=email, password=PASSWORD, adult_attested=True)


def test_get_subject_id_for_user_returns_the_linked_subject():
    user = make_user()
    subject_id = services.get_subject_id_for_user(user)
    assert isinstance(subject_id, uuid.UUID)
    assert subject_id == SubjectLink.objects.get(user=user).subject_id


def test_each_user_gets_a_different_subject():
    a, b = make_user("a@example.com"), make_user("b@example.com")
    assert services.get_subject_id_for_user(a) != services.get_subject_id_for_user(b)


def test_subject_id_is_not_the_user_id():
    user = make_user()
    assert services.get_subject_id_for_user(user) != user.id


def test_deleting_a_user_unlinks_but_keeps_the_subject():
    user = make_user()
    subject_id = services.get_subject_id_for_user(user)
    user.delete()
    assert not SubjectLink.objects.exists()
    assert Subject.objects.filter(id=subject_id).exists()


def test_subject_with_a_link_cannot_be_deleted():
    user = make_user()
    with pytest.raises(ProtectedError):
        Subject.objects.get(link__user=user).delete()


def test_failed_duplicate_registration_leaves_no_orphan_subject():
    make_user()
    with pytest.raises(services.EmailAlreadyRegistered):
        make_user("ADA@example.com")
    assert Subject.objects.count() == 1


def test_adult_attestation_must_be_exactly_true():
    for value in (False, None, "true", 1):
        with pytest.raises(services.AdultAttestationRequired):
            services.register_user(email="x@example.com", password=PASSWORD, adult_attested=value)
    assert not User.objects.exists()


def test_database_rejects_non_lowercase_email():
    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.bulk_create([User(email="Mixed@Example.com")])


def test_database_rejects_duplicate_email():
    make_user()
    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.bulk_create([User(email="ada@example.com")])


def test_password_is_hashed():
    user = make_user()
    assert user.password != PASSWORD
    assert user.password.startswith(("pbkdf2_", "argon2", "bcrypt", "scrypt"))
