from knox.auth import TokenAuthentication
from knox.models import AuthToken
from knox.views import LogoutView as KnoxLogoutView
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LoginSerializer, RegistrationSerializer, UserProfileUpdateSerializer
from .throttles import LoginThrottle, RegisterThrottle
from .utils import build_auth_response, ensure_user_profile, hash_client_ip


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [RegisterThrottle]

    def post(self, request, *args, **kwargs):
        serializer = RegistrationSerializer(data=request.data, context={'ip_hash': hash_client_ip(request)})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        _, token = AuthToken.objects.create(user)
        return Response(build_auth_response(user, token), status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [LoginThrottle]

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        ensure_user_profile(user)
        _, token = AuthToken.objects.create(user)
        return Response(build_auth_response(user, token), status=status.HTTP_200_OK)


class LogoutView(KnoxLogoutView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]


class ProfileView(generics.RetrieveUpdateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserProfileUpdateSerializer

    def get_object(self):
        return ensure_user_profile(self.request.user)
