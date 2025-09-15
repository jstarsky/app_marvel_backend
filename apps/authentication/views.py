from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken, UntypedToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.hashers import check_password
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
        
        try:
            serializer.is_valid(raise_exception=True)
            return success_response(
                data=serializer.validated_data
            )
        except Exception as e:
            return error_response(
                message="invalid_credentials",
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
        
        # Generate tokens for the new user
        refresh = RefreshToken.for_user(user)
        
        return success_response(
            data={
                'user': UserSerializer(user).data,
                'token': str(refresh.access_token),
            },
            status_code=status.HTTP_201_CREATED
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
    serializer = UserSerializer(request.user)
    return success_response(
        data=serializer.data
    )

@api_view(['PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def update_profile(request):
    """
    Update current user profile
    """
    serializer = UserSerializer(request.user, data=request.data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        return success_response(
            data=serializer.data
        )
    
    return error_response(
        message="Update failed",
        errors=serializer.errors,
        status_code=status.HTTP_400_BAD_REQUEST
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