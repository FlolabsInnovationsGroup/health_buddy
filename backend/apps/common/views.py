from django.db.transaction import non_atomic_requests
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .health import database_is_reachable


# Health checks run outside the per-request transaction (ATOMIC_REQUESTS): the liveness
# probe must not need the database, and the readiness probe must still answer 503
# (not crash with a 500) when the database is down.
@non_atomic_requests
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def liveness(request):
    """The process is up. Does not touch the database."""
    return Response({"status": "ok"})


@non_atomic_requests
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def database(request):
    """The process can reach the database."""
    if database_is_reachable():
        return Response({"status": "ok"})
    return Response({"status": "unavailable"}, status=503)
