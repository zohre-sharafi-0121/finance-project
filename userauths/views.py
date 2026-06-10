# --- Imports: we pull in tools we need from Django, DRF, and SimpleJWT ---

from django.contrib.auth import authenticate  # Built-in helper to check email/password and return a user
from django.conf import settings              # Access to project settings (e.g., SIMPLE_JWT config)
from django.http import HttpRequest           # Type hint for Django request objects

from rest_framework.views import APIView      # Base class for DRF views
from rest_framework.response import Response  # Standard DRF HTTP response wrapper
from rest_framework import status             # Handy HTTP status codes (200, 400, etc.)
from rest_framework.permissions import IsAuthenticated  # Permission class requiring a valid login

from rest_framework_simplejwt.views import TokenRefreshView as SimpleJWTTokenRefreshView  # Built-in token refresh view
from rest_framework_simplejwt.serializers import TokenRefreshSerializer                   # Default refresh serializer
from rest_framework_simplejwt.tokens import RefreshToken                                  # Object for creating/handling JWT refresh tokens
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken                  # Errors thrown for bad/expired tokens
from rest_framework import status, permissions                                            # Re-import (status already imported), plus permissions alias

from userauths import serializers as userauths_serializers  # Your app's serializers (aliased for clarity)
from userauths import models as userauths_models            # Your app's models (aliased for clarity)
# from core import models as core_models                      # Example: other app models (not used below but imported)


class RegisterView(APIView):
    def post(self, request):
        serializer = userauths_serializers.UserRegisterSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            user = serializer.save()

            refresh = RefreshToken.for_user(user)

            response_data = {
                'access': str(refresh.access_token),
                'message': "User registered and logged in successfully"
            }

            response = Response(response_data, status=status.HTTP_201_CREATED)

            response.set_cookie(
                key="refresh",
                value=str(refresh),
                httponly=True,
                max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),  # Cookie lifetime in seconds
                samesite=settings.SIMPLE_JWT.get('AUTH_COOKIE_SAMESITE', 'Lax'),  # Restrict cross-site sending
                secure=settings.SIMPLE_JWT.get('AUTH_COOKIE_SECURE', not settings.DEBUG),  # HTTPS-only in prod
            )

            return response
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class LoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"error", "Please provide both email and password"}, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(username=email, password=password)

        if user:
            refresh = RefreshToken.for_user(user)

            response_data = {
                'access': str(refresh.access_token),
            }

            response = Response(response_data, status=status.HTTP_200_OK)

            response.set_cookie(
                key="refresh",
                value=str(refresh),
                httponly=True,
                max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),  # Cookie lifetime in seconds
                samesite=settings.SIMPLE_JWT.get('AUTH_COOKIE_SAMESITE', 'Lax'),  # Restrict cross-site sending
                secure=settings.SIMPLE_JWT.get('AUTH_COOKIE_SECURE', not settings.DEBUG),  # HTTPS-only in prod
            )

            return response
        
        return Response({"error": "Invalid Credentials"}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    def post(self, request):
        refresh_token = request.COOKIES.get("refresh")

        if not refresh_token:
            return Response({"error", "Refresh token not found"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            response = Response({"message", "Logout successful"}, status=status.HTTP_200_OK)
            response.delete_cookie("refresh")

            return response
        except (TokenError, InvalidToken):
            return Response({"error", "Invalid or expired refresh token"}, status=status.HTTP_400_BAD_REQUEST)
            

class UserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = userauths_serializers.UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    


class CookieTokenRefreshSerializer(TokenRefreshSerializer):
    """
    This custom serializer reads the refresh token from the httpOnly cookie.
    """
    # We don’t expect the client to send 'refresh' in the body; we'll inject it from the request cookie
    refresh = None # We will get it from the request context instead.

    def validate(self, attrs):
        # Pull the refresh token from the request's cookies and place it into attrs so parent logic works
        attrs['refresh'] = self.context['request'].COOKIES.get('refresh', None)

        # If there’s no cookie, we can’t refresh—throw a clear error
        if attrs['refresh'] is None:
            raise InvalidToken('No valid refresh token found in cookie.')
        
        # Delegate the rest (signature checks, expiry, rotation logic) to the parent serializer
        return super().validate(attrs)


class CookieTokenRefreshView(SimpleJWTTokenRefreshView):
    """
    This view overrides the default TokenRefreshView to work with httpOnly cookies.
    """
    # Use our custom serializer that reads the cookie instead of expecting JSON input
    serializer_class = CookieTokenRefreshSerializer

    def post(self, request, *args, **kwargs):
        # Call the original post method to perform the actual refresh logic
        response = super().post(request, *args, **kwargs)
        
        # If the refresh succeeded, response.data may include:
        # - a new access token (always)
        # - possibly a new refresh token (if rotation is enabled)
        # We move any new refresh token into a secure cookie and remove it from the JSON body.
        if response.status_code == 200 and 'refresh' in response.data:
            # Pop removes 'refresh' from the body and returns it
            refresh_token = response.data.pop('refresh', None)
            
            # Store the rotated refresh token back into httpOnly cookie (safer than exposing in JSON)
            response.set_cookie(
                key='refresh',
                value=str(refresh_token),
                httponly=True,
                max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
                samesite=settings.SIMPLE_JWT.get('AUTH_COOKIE_SAMESITE', 'Lax'),
                secure=settings.SIMPLE_JWT.get('AUTH_COOKIE_SECURE', not settings.DEBUG),
            )
        
        # Return the response with access token in body and refresh in cookie
        return response


class KYCView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        kyc = userauths_models.KYC.objects.get(user=request.user)
        serializer = userauths_serializers.KYCSerializer(kyc)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class KYCCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = userauths_serializers.KYCCreateSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            kyc = serializer.save()

            return Response({
                "message": "KYC Created successfully",
                "kyc": {
                    "full_name": kyc.full_name,
                    "date_of_birth": kyc.date_of_birth,
                    "id_type": kyc.id_type,
                    "id_image": kyc.id_image,
                    "verification_status": kyc.verification_status,  # starts as UNVERIFIED
                    "created_at": kyc.created_at,
                    "updated_at": kyc.updated_at,
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)