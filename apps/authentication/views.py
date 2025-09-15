from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken, UntypedToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.hashers import check_password
from django.db.utils import OperationalError
from utils.responses import success_response, error_response
from .serializers import (
    UserRegistrationSerializer, 
    CustomTokenObtainPairSerializer,
    UserSerializer,
    PasswordChangeSerializer
)

User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        # Run validation and return tokens+user on success.
        # Be careful: accessing `serializer.errors` before `is_valid()` runs
        # raises an AssertionError in DRF. Call `is_valid()` and handle
        # validation or OperationalError from token creation separately.
        try:
            serializer.is_valid(raise_exception=True)
            return success_response(
                data=serializer.validated_data
            )
        except OperationalError as oe:
            # Token creation may attempt to write OutstandingToken (blacklist)
            # which requires migrations. Surface a clear admin-guidance message.
            return error_response(
                message=(
                    "tokens_unavailable: token storage not ready; ensure "
                    "'rest_framework_simplejwt.token_blacklist' is migrated"
                ),
                errors=str(oe),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception:
            # Validation failed. Only access `errors` property now that
            # `is_valid()` was called (or raised). If there are no errors,
            # fall back to a generic invalid_credentials message.
            errors = getattr(serializer, '_errors', None) or getattr(serializer, 'errors', None)
            return error_response(
                message="invalid_credentials",
                errors=errors,
                status_code=status.HTTP_401_UNAUTHORIZED
            )

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register_user(request):
    """
    Register a new user
    """
    serializer = UserRegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        # Try to generate tokens for the new user. If token_blacklist tables
        # haven't been migrated (OperationalError), return success without
        # tokens and instruct admin to run migrations.
        try:
            refresh = RefreshToken.for_user(user)
            token_data = {'token': str(refresh.access_token)}
            extra_msg = None
        except OperationalError:
            token_data = {}
            extra_msg = (
                "tokens_unavailable: ensure 'rest_framework_simplejwt.token_blacklist' "
                "is migrated"
            )

        response_data = {'user': UserSerializer(user).data}
        response_data.update(token_data)

        return success_response(
            data=response_data,
            status_code=status.HTTP_201_CREATED,
            message=extra_msg if extra_msg else None
        )
    
    return error_response(
        message="registration_failed",
        errors=serializer.errors,
        status_code=status.HTTP_400_BAD_REQUEST
    )

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_profile(request):
    """
    Get current user profile
    """
    # Profile endpoints are disabled in production to avoid depending on the
    # optional `UserProfile` model and its migrations. Return a clear message
    # so clients don't mistake this for an internal error.
    return error_response(
        message="profile_endpoints_disabled",
        status_code=status.HTTP_404_NOT_FOUND
    )

@api_view(['PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def update_profile(request):
    """
    Update current user profile
    """
    # Profile update is disabled to avoid touching the optional profile table.
    return error_response(
        message="profile_endpoints_disabled",
        status_code=status.HTTP_404_NOT_FOUND
    )

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):
    """
    Change user password
    """
    serializer = PasswordChangeSerializer(data=request.data)
    
    if serializer.is_valid():
        user = request.user

        if not check_password(serializer.validated_data['old_password'], user.password):
            return error_response(
                message="Old password is incorrect",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(serializer.validated_data['new_password'])
        user.save()

        return success_response()

    return error_response(
        message="Password change failed",
        errors=serializer.errors,
        status_code=status.HTTP_400_BAD_REQUEST
    )

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_user(request):
    """
    Logout user using only the Bearer access token (no request body required).
    This blacklists all outstanding refresh tokens for the user associated with
    the provided access token (global logout for that user).
    """
    try:
        # Require Authorization header with Bearer token
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return error_response(
                message="Authorization Bearer token required",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        access_token = auth_header.split()[1]

        try:
            # Validate the token (will raise if invalid/expired)
            untoken = UntypedToken(access_token)
        except (TokenError, InvalidToken) as exc:
            return error_response(
                message="Invalid or expired token",
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        user_id = untoken.payload.get('user_id') or untoken.payload.get('user')
        if not user_id:
            return error_response(
                message="Token missing user information",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.filter(id=user_id).first()
        if not user:
            return error_response(
                message="User not found",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Blacklist all outstanding refresh tokens for the user (global logout)
        try:
            # If the token_blacklist app isn't installed or migrations haven't run,
            # OutstandingToken may not have a manager. Detect that and return
            # a clear administrative error instead of raising AttributeError.
            if not hasattr(OutstandingToken, 'objects'):
                return error_response(
                    message=(
                        "Token blacklist unavailable: ensure 'rest_framework_simplejwt.token_blacklist' "
                        "is in INSTALLED_APPS and run 'python manage.py migrate'"
                    ),
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            for outstanding in OutstandingToken.objects.filter(user=user):
                BlacklistedToken.objects.get_or_create(token=outstanding)
        except Exception as e:
            # More specific feedback if blacklisting/storage fails
            return error_response(
                message=f"Failed to blacklist tokens: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return success_response()
    except Exception as e:
        # Return exception text to help debugging client-side issues
        return error_response(
            message=f"Logout failed: {str(e)}",
            status_code=status.HTTP_400_BAD_REQUEST
        )