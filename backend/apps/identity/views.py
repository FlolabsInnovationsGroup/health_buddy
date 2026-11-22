from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
)

from . import services
from .serializers import RegisterSerializer, UserSerializer


class RegisterView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            user = services.register_user(
                email=data["email"],
                password=data["password"],
                display_name=data["display_name"],
                adult_attested=data["adult_attested"],
            )
        except services.AdultAttestationRequired:
            return Response(
                {"adult_attested": ["You must confirm you are 18 or older to create an account."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except services.EmailAlreadyRegistered:
            return Response(
                {"email": ["An account with this email already exists."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except DjangoValidationError as exc:
            return Response({"password": exc.messages}, status=status.HTTP_400_BAD_REQUEST)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class ThrottledTokenObtainPairView(TokenObtainPairView):
    throttle_scope = "auth"


class ThrottledTokenRefreshView(TokenRefreshView):
    throttle_scope = "auth"


class ThrottledLogoutView(TokenBlacklistView):
    """Revokes a refresh token. Holding the token is the proof, so no access token is needed."""

    throttle_scope = "auth"
