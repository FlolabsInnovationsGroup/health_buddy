from django.urls import path

from . import views

urlpatterns = [
    path("", views.liveness, name="health-live"),
    path("db/", views.database, name="health-db"),
]
