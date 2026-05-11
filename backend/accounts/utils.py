import hashlib

from .models import UserProfile
from .username_generator import generate_unique_username



def hash_client_ip(request) -> str:
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
    ip = forwarded_for.split(',')[0].strip() if forwarded_for else request.META.get('REMOTE_ADDR', '').strip()
    if not ip:
        return ''
    return hashlib.sha256(ip.encode('utf-8')).hexdigest()



def ensure_user_profile(user):
    if hasattr(user, 'profile'):
        return user.profile
    username = user.username or generate_unique_username()
    return UserProfile.objects.create(user=user, username=username)



def build_auth_response(user, token: str) -> dict:
    profile = ensure_user_profile(user)
    return {
        'token': token,
        'user': {
            'id': user.id,
            'username': user.username,
            'is_staff': user.is_staff,
        },
        'profile': {
            'id': profile.id,
            'username': profile.username,
            'age_range': profile.age_range,
            'country': profile.country,
            'us_state': profile.us_state,
            'gender': profile.gender,
            'created_at': profile.created_at,
        },
    }
