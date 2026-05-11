from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('username', 'user', 'country', 'us_state', 'created_at')
    search_fields = ('username', 'user__email', 'user__username')
    list_filter = ('country', 'us_state', 'created_at')
    readonly_fields = ('created_at',)
    raw_id_fields = ('user',)
