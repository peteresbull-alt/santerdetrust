"""
Authentication views for login, logout, and token refresh
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from django.contrib.auth import authenticate
from django.conf import settings
from django.utils import timezone


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Authenticate user and set JWT tokens in HTTP-only cookies.
    
    Request body:
        {
            "email": "user@example.com",
            "password": "yourpassword"
        }
    
    Response:
        {
            "message": "Login successful",
            "user": {
                "id": int,
                "email": "string",
                "first_name": "string",
                "last_name": "string",
                "bank_id": "string"
            }
        }
    """
    # Accept both 'email' and 'username' for flexibility
    email = request.data.get('email') or request.data.get('username')
    password = request.data.get('password')
    
    if not email or not password:
        return Response(
            {'error': 'Please provide both email and password'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Authenticate user (Django will use email since USERNAME_FIELD = 'email')
    user = authenticate(request, username=email, password=password)
    
    if user is None:
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    if not user.is_active:
        return Response(
            {'error': 'Account is disabled'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Generate tokens
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)
    
    # Prepare response with user data
    response = Response({
        'message': 'Login successful',
        'user': {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.get_full_name,
            'bank_id': user.bank_id,
            'customer_id': user.customer_id,
            'phone_number': user.phone_number,
            'account_status': user.account_status,
            'has_verified_kyc': user.has_verified_kyc,
            'profile_image': user.profile_image.url if user.profile_image else None,
        }
    }, status=status.HTTP_200_OK)
    
    # Set tokens in HTTP-only cookies
    # Access token cookie
    response.set_cookie(
        key='access_token',
        value=access_token,
        max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
        httponly=True,  # Cannot be accessed by JavaScript
        secure=not settings.DEBUG,  # HTTPS only in production
        samesite='Lax' if settings.DEBUG else 'None',  # CSRF protection
        domain=None,  # Current domain
    )
    
    # Refresh token cookie
    response.set_cookie(
        key='refresh_token',
        value=refresh_token,
        max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
        httponly=True,
        secure=not settings.DEBUG,
        samesite='Lax' if settings.DEBUG else 'None',
        domain=None,
    )
    
    return response


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """
    Register a new user.
    
    Request body:
        {
            "email": "user@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "+1234567890",
            "password": "securepassword",
            "confirm_password": "securepassword"
        }
    
    Response:
        {
            "message": "Registration successful",
            "user": {
                "id": int,
                "email": "string",
                "first_name": "string",
                "last_name": "string"
            }
        }
    """
    from app.models import CustomUser
    
    # Get data from request
    email = request.data.get('email')
    first_name = request.data.get('first_name')
    last_name = request.data.get('last_name')
    phone_number = request.data.get('phone_number')
    password = request.data.get('password')
    confirm_password = request.data.get('confirm_password')
    
    # Validate required fields
    if not all([email, first_name, last_name, phone_number, password]):
        return Response(
            {'error': 'All fields are required: email, first_name, last_name, phone_number, password'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate password match
    if password != confirm_password:
        return Response(
            {'error': 'Passwords do not match'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate password length
    if len(password) < 8:
        return Response(
            {'error': 'Password must be at least 8 characters long'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if user already exists
    if CustomUser.objects.filter(email=email).exists():
        return Response(
            {'error': 'User with this email already exists'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if phone number already exists
    if CustomUser.objects.filter(phone_number=phone_number).exists():
        return Response(
            {'error': 'User with this phone number already exists'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Create user
        user = CustomUser.objects.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            password=password
        )
        
        # Generate tokens for auto-login after registration
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        # Prepare response
        response = Response({
            'message': 'Registration successful',
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'full_name': user.get_full_name,
                'bank_id': user.bank_id,
                'customer_id': user.customer_id,
                'phone_number': user.phone_number,
            }
        }, status=status.HTTP_201_CREATED)
        
        # Set tokens in cookies (auto-login)
        response.set_cookie(
            key='access_token',
            value=access_token,
            max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax' if settings.DEBUG else 'None',
            domain=None,
        )
        
        response.set_cookie(
            key='refresh_token',
            value=refresh_token,
            max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax' if settings.DEBUG else 'None',
            domain=None,
        )
        
        return response
        
    except Exception as e:
        return Response(
            {'error': f'Registration failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Logout user by blacklisting the refresh token and clearing cookies.
    
    Response:
        {
            "message": "Logout successful"
        }
    """
    try:
        # Get refresh token from cookie
        refresh_token = request.COOKIES.get('refresh_token')
        
        if refresh_token:
            # Blacklist the refresh token
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        # Prepare response
        response = Response({
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)
        
        # Delete cookies
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        
        return response
        
    except TokenError:
        # Even if token is invalid, still clear cookies
        response = Response({
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)
        
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        
        return response
    
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token_view(request):
    """
    Refresh the access token using the refresh token from cookies.
    
    Response:
        {
            "message": "Token refreshed successfully"
        }
    """
    # Get refresh token from cookie
    refresh_token = request.COOKIES.get('refresh_token')
    
    if not refresh_token:
        return Response(
            {'error': 'Refresh token not found'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        # Validate and refresh the token
        refresh = RefreshToken(refresh_token)
        
        # Get new access token
        new_access_token = str(refresh.access_token)
        
        # If ROTATE_REFRESH_TOKENS is True, get new refresh token
        if settings.SIMPLE_JWT.get('ROTATE_REFRESH_TOKENS'):
            new_refresh_token = str(refresh)
        else:
            new_refresh_token = refresh_token
        
        # Prepare response
        response = Response({
            'message': 'Token refreshed successfully'
        }, status=status.HTTP_200_OK)
        
        # Set new access token cookie
        response.set_cookie(
            key='access_token',
            value=new_access_token,
            max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax' if settings.DEBUG else 'None',
            domain=None,
        )
        
        # Set new refresh token cookie if rotated
        if settings.SIMPLE_JWT.get('ROTATE_REFRESH_TOKENS'):
            response.set_cookie(
                key='refresh_token',
                value=new_refresh_token,
                max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax' if settings.DEBUG else 'None',
                domain=None,
            )
        
        return response
        
    except TokenError as e:
        return Response(
            {'error': 'Invalid or expired refresh token'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verify_token_view(request):
    """
    Verify if the current access token is valid.
    
    Response:
        {
            "message": "Token is valid",
            "user": {
                "id": int,
                "email": "string",
                "first_name": "string",
                "last_name": "string"
            }
        }
    """
    return Response({
        'message': 'Token is valid',
        'user': {
            'id': request.user.id,
            'email': request.user.email,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'full_name': request.user.get_full_name,
            'bank_id': request.user.bank_id,
            'customer_id': request.user.customer_id,
            'account_status': request.user.account_status,
        }
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_view(request):
    """
    Get current authenticated user information.
    
    Response:
        {
            "user": {
                "id": int,
                "email": "string",
                "first_name": "string",
                "last_name": "string",
                "phone_number": "string",
                "bank_id": "string",
                "customer_id": "string",
                "account_status": "string",
                "has_verified_kyc": boolean,
                "total_balance": "decimal"
            }
        }
    """
    user = request.user
    
    return Response({
        'user': {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'middle_name': user.middle_name,
            'last_name': user.last_name,
            'full_name': user.get_full_name,
            'phone_number': user.phone_number,
            'alternate_phone': user.alternate_phone,
            'bank_id': user.bank_id,
            'customer_id': user.customer_id,
            'date_of_birth': user.date_of_birth,
            'gender': user.gender,
            'address': user.address,
            'city': user.city,
            'state': user.state,
            'country': user.country,
            'postal_code': user.postal_code,
            'account_status': user.account_status,
            'has_verified_kyc': user.has_verified_kyc,
            'email_verified': user.email_verified,
            'phone_verified': user.phone_verified,
            'two_factor_enabled': user.two_factor_enabled,
            'preferred_currency': user.preferred_currency,
            'total_balance': str(user.get_total_balance),
            'can_apply_for_loans': user.can_apply_for_loans,
            'can_apply_for_cards': user.can_apply_for_cards,
            'can_make_transfers': user.can_make_transfers,
            'profile_image': user.profile_image.url if user.profile_image else None,
            'is_staff': user.is_staff,
            'date_joined': user.date_joined,
        }
    }, status=status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_profile_view(request):
    """
    Update user profile information.
    
    Request body (all fields optional):
        {
            "first_name": "string",
            "middle_name": "string",
            "last_name": "string",
            "phone_number": "string",
            "alternate_phone": "string",
            "date_of_birth": "YYYY-MM-DD",
            "gender": "string",
            "address": "string",
            "city": "string",
            "state": "string",
            "country": "string",
            "postal_code": "string"
        }
    
    Response:
        {
            "message": "Profile updated successfully",
            "user": {...}
        }
    """
    user = request.user
    
    # Update allowed fields
    allowed_fields = [
        'first_name', 'middle_name', 'last_name', 'phone_number', 
        'alternate_phone', 'date_of_birth', 'gender', 'address', 
        'address_line2', 'city', 'state', 'country', 'postal_code',
        'marital_status', 'number_of_dependents', 'nationality'
    ]
    
    for field in allowed_fields:
        if field in request.data:
            setattr(user, field, request.data[field])
    
    try:
        user.save()
        
        return Response({
            'message': 'Profile updated successfully',
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'middle_name': user.middle_name,
                'last_name': user.last_name,
                'full_name': user.get_full_name,
                'phone_number': user.phone_number,
                'alternate_phone': user.alternate_phone,
                'date_of_birth': user.date_of_birth,
                'gender': user.gender,
                'address': user.address,
                'city': user.city,
                'state': user.state,
                'country': user.country,
                'postal_code': user.postal_code,
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Profile update failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    """
    Change user password.
    
    Request body:
        {
            "old_password": "string",
            "new_password": "string",
            "confirm_password": "string"
        }
    
    Response:
        {
            "message": "Password changed successfully"
        }
    """
    user = request.user
    
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')
    confirm_password = request.data.get('confirm_password')
    
    # Validate inputs
    if not all([old_password, new_password, confirm_password]):
        return Response(
            {'error': 'All fields are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check old password
    if not user.check_password(old_password):
        return Response(
            {'error': 'Old password is incorrect'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check password match
    if new_password != confirm_password:
        return Response(
            {'error': 'New passwords do not match'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate password length
    if len(new_password) < 8:
        return Response(
            {'error': 'New password must be at least 8 characters long'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Change password
    user.set_password(new_password)
    user.password_changed_at = timezone.now()
    user.save()
    
    return Response({
        'message': 'Password changed successfully'
    }, status=status.HTTP_200_OK)