import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def _clear_cache():
    # Throttle counters live in the cache. Reset them so tests do not affect each other.
    cache.clear()
    yield
    cache.clear()
