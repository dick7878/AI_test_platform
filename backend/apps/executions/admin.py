from django.contrib import admin

from .models import ExecutionResult, ExecutionTask


@admin.register(ExecutionTask)
class ExecutionTaskAdmin(admin.ModelAdmin):
    list_display = ("id", "project", "status", "trigger", "started_at", "finished_at")
    search_fields = ("project__name", "status", "trigger")


@admin.register(ExecutionResult)
class ExecutionResultAdmin(admin.ModelAdmin):
    list_display = ("id", "task", "status", "duration", "created_at")
    search_fields = ("status", "error_message")
