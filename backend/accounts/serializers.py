from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from legal.models import TermsAcceptance, TermsOfUseVersion

from .models import UserProfile
from .username_generator import generate_unique_username, is_username_available, validate_public_username

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('id', 'username', 'age_range', 'country', 'us_state', 'gender', 'created_at')
        read_only_fields = ('id', 'username', 'created_at')


class RegistrationSerializer(serializers.Serializer):
    username = serializers.CharField(required=False, allow_blank=True, max_length=50)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    age_range = serializers.CharField(required=False, allow_blank=True, max_length=20)
    country = serializers.CharField(required=False, allow_blank=True, max_length=2)
    us_state = serializers.CharField(required=False, allow_blank=True, max_length=2)
    gender = serializers.CharField(required=False, allow_blank=True, max_length=30)
    terms_version = serializers.CharField(max_length=20)
    terms_accepted = serializers.BooleanField()

    def validate_username(self, value):
        if not value:
            return ''
        try:
            normalized = validate_public_username(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc
        if not is_username_available(normalized):
            raise serializers.ValidationError('That username is already taken.')
        return normalized

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        if attrs.get('terms_accepted') is not True:
            raise serializers.ValidationError({'terms_accepted': ['You must accept the active terms of use.']})
        try:
            attrs['terms_version_obj'] = TermsOfUseVersion.objects.get(version=attrs['terms_version'], is_active=True)
        except TermsOfUseVersion.DoesNotExist as exc:
            raise serializers.ValidationError({'terms_version': ['An active terms version matching this value was not found.']}) from exc
        return attrs

    def create(self, validated_data):
        validated_data = validated_data.copy()
        terms_version = validated_data.pop('terms_version_obj')
        validated_data.pop('terms_version', None)
        validated_data.pop('terms_accepted', None)
        username = validated_data.pop('username', '') or generate_unique_username()
        password = validated_data.pop('password')
        ip_hash = self.context.get('ip_hash', '')

        with transaction.atomic():
            user = User.objects.create(username=username)
            user.set_password(password)
            user.save(update_fields=['password'])
            UserProfile.objects.create(user=user, username=username, **validated_data)
            TermsAcceptance.objects.create(user=user, terms_version=terms_version, ip_hash=ip_hash)
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=50)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        user = authenticate(username=attrs.get('username'), password=attrs.get('password'))
        if not user:
            raise serializers.ValidationError({'non_field_errors': ['Invalid username or password.']})
        attrs['user'] = user
        return attrs


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(read_only=True)

    class Meta:
        model = UserProfile
        fields = ('id', 'username', 'age_range', 'country', 'us_state', 'gender', 'created_at')
        read_only_fields = ('id', 'username', 'created_at')

    def validate(self, attrs):
        if 'username' in self.initial_data:
            raise serializers.ValidationError({'username': ['Username cannot be changed after registration.']})
        return attrs
