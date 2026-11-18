from django.urls import include, path

urlpatterns = [
    path("health/", include("apps.common.urls")),
]
