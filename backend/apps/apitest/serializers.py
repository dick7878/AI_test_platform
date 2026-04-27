from rest_framework import serializers

from .models import ApiTestCase


class ApiTestCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiTestCase
        fields = [
            "id",
            "project",
            "title",
            "description",
            "status",
            "method",
            "path",
            "headers",
            "query_params",
            "body",
            "script",
            "last_run_status",
            "last_run_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "last_run_status", "last_run_at", "created_at", "updated_at"]
