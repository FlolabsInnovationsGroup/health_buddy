from rest_framework import serializers

from .models import User


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(write_only=True, trim_whitespace=False, max_length=128)
    display_name = serializers.CharField(
        max_length=150, required=False, allow_blank=True, default=""
    )
    adult_attested = serializers.BooleanField()


class UserSerializer(serializers.ModelSerializer):
    # The subject id is deliberately not exposed. It stays on the server side.
    class Meta:
        model = User
        fields = ["id", "email", "display_name", "date_joined"]
        read_only_fields = fields
