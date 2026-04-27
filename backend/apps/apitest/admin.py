from django.contrib import admin

from .models import ApiEnvironment


@admin.register(ApiEnvironment)
class ApiEnvironmentAdmin(admin.ModelAdmin):
    list_display = ("id", "project", "name", "base_url", "created_at", "updated_at")
    search_fields = ("project__name", "name", "base_url")
