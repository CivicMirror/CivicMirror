import pytest
from django.contrib.auth import get_user_model

from accounts.models import UserProfile
from legal.models import TermsAcceptance

User = get_user_model()


@pytest.mark.django_db
def test_registration_creates_profile_terms_and_token(api_client, active_terms):
    response = api_client.post(
        "/api/auth/register/",
        {
            "password": "StrongPass123!",
            "age_range": "25-34",
            "country": "US",
            "us_state": "MA",
            "gender": "nonbinary",
            "terms_version": active_terms.version,
            "terms_accepted": True,
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.data["token"]
    assert response.data["profile"]["username"]
    assert User.objects.count() == 1
    assert UserProfile.objects.count() == 1
    assert TermsAcceptance.objects.count() == 1


@pytest.mark.django_db
def test_registration_requires_active_terms(api_client):
    response = api_client.post(
        "/api/auth/register/",
        {
            "username": "sample_user",
            "password": "StrongPass123!",
            "terms_version": "9999-99",
            "terms_accepted": True,
        },
        format="json",
    )

    assert response.status_code == 400
    assert "terms_version" in response.data["errors"]


@pytest.mark.django_db
def test_login_and_profile_patch(api_client, active_terms):
    user = User.objects.create_user(username="teal_osprey_4821", password="StrongPass123!")
    UserProfile.objects.create(user=user, username=user.username, country="US", us_state="MA")

    login_response = api_client.post(
        "/api/auth/login/",
        {"username": user.username, "password": "StrongPass123!"},
        format="json",
    )

    assert login_response.status_code == 200
    token = login_response.data["token"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {token}")

    patch_response = api_client.patch(
        "/api/users/me/profile/",
        {"age_range": "35-44", "gender": "female"},
        format="json",
    )

    assert patch_response.status_code == 200
    assert patch_response.data["age_range"] == "35-44"
    assert patch_response.data["gender"] == "female"

    invalid_patch = api_client.patch(
        "/api/users/me/profile/",
        {"username": "new_name"},
        format="json",
    )
    assert invalid_patch.status_code == 400
    assert "username" in invalid_patch.data["errors"]
