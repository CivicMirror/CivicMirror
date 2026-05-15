import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from legal.models import TermsOfUseVersion


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def active_terms(db):
    obj, _ = TermsOfUseVersion.objects.get_or_create(
        version="2025-01",
        defaults={
            "content_checksum": "abc123",
            "published_at": timezone.now(),
            "is_active": True,
        },
    )
    return obj
