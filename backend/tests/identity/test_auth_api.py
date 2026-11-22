import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from apps.identity.models import Subject, SubjectLink, User

PASSWORD = "a-long-test-passphrase-42"
REGISTER = "/api/v1/auth/register/"
TOKEN = "/api/v1/auth/token/"
REFRESH = "/api/v1/auth/token/refresh/"
LOGOUT = "/api/v1/auth/logout/"
ME = "/api/v1/auth/me/"

pytestmark = pytest.mark.django_db


@pytest.fixture
def api():
    return APIClient()


def register(api, **overrides):
    payload = {
        "email": "Ada@Example.com",
        "password": PASSWORD,
        "display_name": "Ada",
        "adult_attested": True,
    }
    payload.update(overrides)
    return api.post(REGISTER, payload, format="json")


def sign_in(api, email="ada@example.com", password=PASSWORD):
    return api.post(TOKEN, {"email": email, "password": password}, format="json")


# --- registration ---------------------------------------------------------------


def test_register_creates_user_and_subject_link(api):
    response = register(api)
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "ada@example.com"
    assert "password" not in body
    assert "subject_id" not in body and "subject" not in body

    user = User.objects.get(email="ada@example.com")
    assert user.adult_attested_at is not None
    assert user.check_password(PASSWORD)
    assert SubjectLink.objects.filter(user=user).count() == 1
    assert Subject.objects.count() == 1


def test_register_requires_adult_attestation(api):
    response = register(api, adult_attested=False)
    assert response.status_code == 400
    assert "adult_attested" in response.json()
    assert not User.objects.exists()
    assert not Subject.objects.exists()


def test_register_requires_adult_attestation_field(api):
    response = api.post(REGISTER, {"email": "a@example.com", "password": PASSWORD}, format="json")
    assert response.status_code == 400
    assert not User.objects.exists()


def test_register_rejects_duplicate_email_ignoring_case(api):
    assert register(api).status_code == 201
    response = register(api, email="ADA@example.COM")
    assert response.status_code == 400
    assert "email" in response.json()
    assert User.objects.count() == 1
    assert Subject.objects.count() == 1


WEAK_PASSWORDS = ["short1", "password1234", "12345678901234", "ada@example.com"]


@pytest.mark.parametrize("password", WEAK_PASSWORDS)
def test_register_rejects_weak_passwords(api, password):
    response = register(api, password=password)
    assert response.status_code == 400
    assert "password" in response.json()
    assert not User.objects.exists()


def test_register_rejects_invalid_email(api):
    assert register(api, email="not-an-email").status_code == 400


def test_register_is_public(api):
    # No credentials at all, and it still works.
    assert register(api).status_code == 201


# --- sign in --------------------------------------------------------------------


def test_sign_in_returns_access_and_refresh_tokens(api):
    register(api)
    response = sign_in(api)
    assert response.status_code == 200
    assert set(response.json()) == {"access", "refresh"}


def test_sign_in_is_case_insensitive_on_email(api):
    register(api)
    assert sign_in(api, email="ADA@EXAMPLE.COM").status_code == 200


def test_sign_in_rejects_wrong_password(api):
    register(api)
    assert sign_in(api, password="wrong-password-123").status_code == 401


def test_sign_in_rejects_unknown_email(api):
    assert sign_in(api, email="nobody@example.com").status_code == 401


def test_sign_in_rejects_inactive_user(api):
    register(api)
    User.objects.update(is_active=False)
    assert sign_in(api).status_code == 401


# --- using the access token -----------------------------------------------------


def test_me_requires_authentication(api):
    assert api.get(ME).status_code == 401


def test_me_returns_current_user_without_subject(api):
    register(api)
    access = sign_in(api).json()["access"]
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    response = api.get(ME)
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "ada@example.com"
    assert set(body) == {"id", "email", "display_name", "date_joined"}


def test_me_rejects_garbage_token(api):
    api.credentials(HTTP_AUTHORIZATION="Bearer not-a-token")
    assert api.get(ME).status_code == 401


def test_refresh_token_is_not_accepted_as_access_token(api):
    register(api)
    refresh = sign_in(api).json()["refresh"]
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh}")
    assert api.get(ME).status_code == 401


def test_access_token_stops_working_when_user_is_deactivated(api):
    register(api)
    access = sign_in(api).json()["access"]
    User.objects.update(is_active=False)
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    assert api.get(ME).status_code == 401


def test_access_token_is_short_lived(settings):
    from datetime import timedelta

    assert settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"] <= timedelta(minutes=15)


# --- refresh and logout ---------------------------------------------------------


def test_refresh_rotates_and_revokes_the_old_refresh_token(api):
    register(api)
    old_refresh = sign_in(api).json()["refresh"]

    first = api.post(REFRESH, {"refresh": old_refresh}, format="json")
    assert first.status_code == 200
    assert first.json()["refresh"] != old_refresh

    reuse = api.post(REFRESH, {"refresh": old_refresh}, format="json")
    assert reuse.status_code == 401


def test_logout_revokes_the_refresh_token(api):
    register(api)
    refresh = sign_in(api).json()["refresh"]
    assert api.post(LOGOUT, {"refresh": refresh}, format="json").status_code == 200
    assert api.post(REFRESH, {"refresh": refresh}, format="json").status_code == 401


def test_logout_rejects_invalid_token(api):
    assert api.post(LOGOUT, {"refresh": "nope"}, format="json").status_code == 401


# --- rate limiting --------------------------------------------------------------


def test_sign_in_is_rate_limited(api):
    cache.clear()
    codes = [
        sign_in(api, email="x@example.com", password="bad-password-123").status_code
        for _ in range(12)
    ]
    assert codes[:10] == [401] * 10
    assert 429 in codes[10:]
