import random
import re

from django.contrib.auth import get_user_model

from .adjectives import ADJECTIVES
from .nouns import NOUNS
from .models import UserProfile

SAFE_USERNAME_RE = re.compile(r'^[a-z0-9_]{3,50}$')
BLOCKED_TERMS = {
    'admin',
    'moderator',
    'support',
    'staff',
    'official',
    'civicmirror',
    'google',
    'electionboard',
}


class UsernameGenerationError(RuntimeError):
    pass



def normalize_username_candidate(value: str) -> str:
    normalized = re.sub(r'[^a-z0-9]+', '_', value.strip().lower()).strip('_')
    normalized = re.sub(r'_+', '_', normalized)
    return normalized



def is_blocked_username(value: str) -> bool:
    return any(term in value for term in BLOCKED_TERMS)



def is_username_available(value: str) -> bool:
    user_model = get_user_model()
    return not UserProfile.objects.filter(username=value).exists() and not user_model.objects.filter(username=value).exists()



def validate_public_username(value: str) -> str:
    normalized = normalize_username_candidate(value)
    if not SAFE_USERNAME_RE.fullmatch(normalized):
        raise ValueError('Username must be 3-50 characters and contain only lowercase letters, numbers, and underscores.')
    if is_blocked_username(normalized):
        raise ValueError('That username is not allowed.')
    return normalized



def generate_unique_username(max_attempts: int = 50) -> str:
    if not ADJECTIVES or not NOUNS:
        raise UsernameGenerationError('Username word lists are empty.')

    for _ in range(max_attempts):
        candidate = f"{random.choice(ADJECTIVES)}_{random.choice(NOUNS)}_{random.randint(0, 9999):04d}"
        if is_blocked_username(candidate):
            continue
        if is_username_available(candidate):
            return candidate
    raise UsernameGenerationError('Unable to generate a unique username.')
