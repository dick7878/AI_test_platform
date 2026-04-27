from rest_framework import serializers


class CreateExecutionTaskRequestSerializer(serializers.Serializer):
    project_id = serializers.IntegerField(min_value=1)
    case_ids = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False,
    )
    env_id = serializers.IntegerField(min_value=1, required=False, allow_null=True)

    def validate_case_ids(self, value: list[str]) -> list[str]:
        for item in value:
            if ":" not in item:
                raise serializers.ValidationError("Each case id must be in '<type>:<id>' format.")
            case_type, raw_id = item.split(":", 1)
            if case_type not in {"api", "ui"}:
                raise serializers.ValidationError("Case type must be 'api' or 'ui'.")
            if not raw_id.isdigit():
                raise serializers.ValidationError("Case id must be numeric.")
        return value


class ExecutionResultItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    content_type = serializers.CharField()
    object_id = serializers.IntegerField()
    status = serializers.CharField()
    duration = serializers.FloatField(allow_null=True)
    logs = serializers.CharField()
    screenshots = serializers.ListField(child=serializers.CharField(), allow_empty=True)
    request_response = serializers.DictField()
    error_message = serializers.CharField(allow_blank=True)
    created_at = serializers.DateTimeField()


class ExecutionTaskResultsResponseSerializer(serializers.Serializer):
    task_id = serializers.IntegerField()
    status = serializers.CharField()
    summary = serializers.JSONField(allow_null=True)
    results = ExecutionResultItemSerializer(many=True)
