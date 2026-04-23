from rest_framework import authentication
from rest_framework import exceptions
from django.contrib.auth.models import User
from .models import Profile
from supabase import create_client, Client
from django.conf import settings

class SupabaseAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]
        
        # Initialize Supabase client
        try:
            supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
        except Exception as e:
            raise exceptions.AuthenticationFailed(f"Backend Supabase configuration error: {str(e)}")
            
        try:
            # Validate token directly with Supabase API
            # This automatically handles key rotation, ECC keys, and expiration securely
            user_response = supabase.auth.get_user(token)
            supabase_user = getattr(user_response, 'user', None)
        except Exception as e:
            raise exceptions.AuthenticationFailed(f"Invalid Token: {str(e)}")

        if not supabase_user:
            raise exceptions.AuthenticationFailed('User not verified by Supabase')

        user_id = supabase_user.id
        email = supabase_user.email or ''

        # Since Supabase handles auth, mirror the user in Django
        user, created = User.objects.get_or_create(username=user_id, defaults={'email': email})
        
        # Ensure profile exists
        Profile.objects.get_or_create(user=user, defaults={'id': user_id, 'full_name': email.split('@')[0] if email else ''})

        return (user, None)
        return (user, None)

    def authenticate_header(self, request):
        return 'Bearer'
