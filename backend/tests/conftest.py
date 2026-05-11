import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from legal.models import TermsOfUseVersion


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def active_terms(db):
    return TermsOfUseVersion.objects.create(
        version="2025-01",
        content_checksum="abc123",
        published_at=timezone.now(),
        is_active=True,
    )
