import pytest
from django.db import OperationalError
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from apps.common import health


def test_liveness_is_public_and_needs_no_database(client):
    # No django_db marker: this fails if the view touches the database.
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.django_db
def test_database_health_ok(client):
    response = client.get("/health/db/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_database_health_returns_503_when_database_is_down(client, monkeypatch):
    monkeypatch.setattr("apps.common.views.database_is_reachable", lambda: False)
    response = client.get("/health/db/")
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}


def test_database_is_reachable_handles_connection_errors(monkeypatch):
    def broken_cursor(*args, **kwargs):
        raise OperationalError("connection refused")

    monkeypatch.setattr(health.connection, "cursor", broken_cursor)
    assert health.database_is_reachable() is False


def test_api_views_deny_by_default():
    class Probe(APIView):
        def get(self, request):
            return Response({})

    response = Probe.as_view()(APIRequestFactory().get("/"))
    assert response.status_code in (401, 403)
