from __future__ import annotations

from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
from rest_framework import permissions, serializers, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class DevLoginRequestSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=128)


class DevLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @csrf_exempt
    def post(self, request: Request) -> Response:
        serializer = DevLoginRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username: str = serializer.validated_data["username"]
        password: str = serializer.validated_data["password"]
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response(
                {"detail": "Invalid username or password."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        login(request, user)
        return Response(
            {
                "id": user.id,
                "username": user.username,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
            },
            status=status.HTTP_200_OK,
        )


class DevLogoutView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @csrf_exempt
    def post(self, request: Request) -> Response:
        logout(request)
        return Response({"detail": "Logged out."}, status=status.HTTP_200_OK)
