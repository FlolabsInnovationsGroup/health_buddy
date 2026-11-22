from django.urls import include, path

urlpatterns = [
    path("health/", include("apps.common.urls")),
    path("api/v1/auth/", include("apps.identity.urls")),
]
