from rest_framework import serializers


class GenerateApiScriptRequestSerializer(serializers.Serializer):
    project_id = serializers.IntegerField(min_value=1)
    interfaces = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False,
    )


class GenerateUiScriptRequestSerializer(serializers.Serializer):
    requirement = serializers.CharField(allow_blank=False, trim_whitespace=True)
