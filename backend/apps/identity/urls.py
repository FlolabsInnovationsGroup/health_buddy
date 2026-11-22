from django.urls import path

from . import views

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="auth-register"),
    path("token/", views.ThrottledTokenObtainPairView.as_view(), name="auth-token"),
    path("token/refresh/", views.ThrottledTokenRefreshView.as_view(), name="auth-token-refresh"),
    path("logout/", views.ThrottledLogoutView.as_view(), name="auth-logout"),
    path("me/", views.MeView.as_view(), name="auth-me"),
]
