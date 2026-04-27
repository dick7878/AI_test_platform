import json

import yaml
from django.db.models import Q
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from apps.apitest.models import ApiTestCase

from .models import Project
from .serializers import ProjectSerializer


class IsProjectMemberPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj) -> bool:
        if obj.owner_id == request.user.id:
            return True
        return obj.projectmember_set.filter(user=request.user).exists()


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectMemberPermission]

    def get_queryset(self):
        user = self.request.user
        return Project.objects.filter(
            Q(owner=user) | Q(projectmember__user=user),
        ).distinct()

    def perform_create(self, serializer) -> None:
        serializer.save(owner=self.request.user)

    @action(
        detail=True,
        methods=["post"],
        url_path="import-swagger",
        parser_classes=[JSONParser, MultiPartParser, FormParser],
    )
    def import_swagger(self, request, pk=None) -> Response:
        project = self.get_object()
        schema = self._load_schema(request)
        created_count = self._create_api_cases(project=project, schema=schema)
        return Response({"created": created_count}, status=status.HTTP_201_CREATED)

    def _load_schema(self, request) -> dict:
        upload_file = request.FILES.get("file")
        if upload_file is not None:
            return self._parse_schema_text(upload_file.read().decode("utf-8"))

        request_data = request.data
        if isinstance(request_data, dict) and "paths" in request_data:
            return request_data

        if isinstance(request_data, dict) and "content" in request_data:
            content = request_data.get("content", "")
            if not isinstance(content, str):
                raise ValidationError({"content": "content must be a string."})
            return self._parse_schema_text(content)

        raise ValidationError("Please provide OpenAPI JSON/YAML content.")

    def _parse_schema_text(self, content: str) -> dict:
        content = content.strip()
        if not content:
            raise ValidationError("Schema content cannot be empty.")

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            parsed = yaml.safe_load(content)

        if not isinstance(parsed, dict):
            raise ValidationError("Schema must parse to an object.")
        return parsed

    def _create_api_cases(self, project: Project, schema: dict) -> int:
        paths = schema.get("paths")
        if not isinstance(paths, dict):
            raise ValidationError({"paths": "paths must be an object."})

        http_methods = ["get", "post", "put", "patch", "delete", "options", "head"]
        case_list = []

        for path, operation_group in paths.items():
            if not isinstance(path, str) or not isinstance(operation_group, dict):
                continue

            for method in http_methods:
                operation = operation_group.get(method)
                if not isinstance(operation, dict):
                    continue

                summary = operation.get("summary")
                description = operation.get("description", "")
                title = summary if isinstance(summary, str) and summary.strip() else f"{method.upper()} {path}"
                case_list.append(
                    ApiTestCase(
                        project=project,
                        title=title,
                        description=description if isinstance(description, str) else "",
                        status=ApiTestCase.DRAFT,
                        method=method.upper(),
                        path=path,
                        script="",
                    )
                )

        ApiTestCase.objects.bulk_create(case_list)
        return len(case_list)
