"""
Custom JWT Authentication that reads tokens from HTTP-only cookies
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from django.conf import settings


class CookieJWTAuthentication(JWTAuthentication):
    """
    Custom authentication class that retrieves JWT tokens from HTTP-only cookies
    instead of the Authorization header.
    
    This provides better security for web applications by storing tokens in
    HTTP-only cookies that cannot be accessed by JavaScript.
    """
    
    def authenticate(self, request):
        """
        Try to authenticate using the access token from cookies.
        
        Args:
            request: The HTTP request object
            
        Returns:
            tuple: (user, validated_token) if authentication succeeds
            None: if no token is found in cookies
            
        Raises:
            InvalidToken: if the token is invalid or expired
        """
        # Try to get access token from cookie
        access_token = request.COOKIES.get('access_token')
        
        if access_token is None:
            return None
        
        # Validate the token
        validated_token = self.get_validated_token(access_token)
        
        # Get the user from the validated token
        return self.get_user(validated_token), validated_token