from django.contrib import admin

from .models import UIEnvironment, UITestCase


@admin.register(UIEnvironment)
class UIEnvironmentAdmin(admin.ModelAdmin):
    list_display = ("id", "project", "name", "target_url", "browser", "viewport")
    search_fields = ("project__name", "name", "target_url")


@admin.register(UITestCase)
class UITestCaseAdmin(admin.ModelAdmin):
    list_display = ("id", "project", "title", "status", "last_run_status", "last_run_at")
    search_fields = ("project__name", "title", "description")
