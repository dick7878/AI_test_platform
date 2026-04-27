from rest_framework import serializers

from .models import UITestCase


class UITestCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = UITestCase
        fields = [
            "id",
            "project",
            "title",
            "description",
            "status",
            "script",
            "elements_snapshot",
            "last_run_status",
            "last_run_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "last_run_status", "last_run_at", "created_at", "updated_at"]
