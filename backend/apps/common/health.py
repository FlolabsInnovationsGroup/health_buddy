"""Health-check logic. Views stay thin and call these functions."""

import logging

from django.db import Error, connection

logger = logging.getLogger(__name__)


def database_is_reachable() -> bool:
    """Return True when the default database answers a trivial query."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Error:
        logger.warning("Database health check failed", exc_info=True)
        return False
    return True
