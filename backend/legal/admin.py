from django.contrib import admin

from .models import TermsAcceptance, TermsOfUseVersion


@admin.register(TermsOfUseVersion)
class TermsOfUseVersionAdmin(admin.ModelAdmin):
    list_display = ('version', 'published_at', 'is_active', 'content_checksum')
    search_fields = ('version', 'content_checksum')
    list_filter = ('is_active', 'published_at')
    ordering = ('-published_at',)


@admin.register(TermsAcceptance)
class TermsAcceptanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'terms_version', 'accepted_at')
    search_fields = ('user__username', 'terms_version__version')
    list_filter = ('terms_version__version', 'accepted_at')
    raw_id_fields = ('user',)
