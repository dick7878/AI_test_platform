from django.contrib import admin

from .models import Project, ProjectMember


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "owner", "notification_url", "created_at", "updated_at")
    search_fields = ("name", "owner__username", "owner__email", "notification_url")


@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = ("id", "project", "user", "created_at", "updated_at")
    search_fields = ("project__name", "user__username", "user__email")
