from django.db import transaction
from django.db.models import Q
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.apitest.models import ApiTestCase
from apps.projects.models import Project

from .serializers import GenerateApiScriptRequestSerializer, GenerateUiScriptRequestSerializer
from .services import GenerateApiScriptByInterfaces, GenerateUiScriptByRequirement


class GenerateApiScriptView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = GenerateApiScriptRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        project_id = serializer.validated_data["project_id"]
        interfaces = serializer.validated_data["interfaces"]

        project = self._get_accessible_project(request_user=request.user, project_id=project_id)
        if project is None:
            return Response({"detail": "Project not found."}, status=status.HTTP_404_NOT_FOUND)

        script = GenerateApiScriptByInterfaces(interfaces=interfaces)

        with transaction.atomic():
            case_queryset = self._match_cases(project_id=project.id, interfaces=interfaces)
            updated_count = case_queryset.update(script=script)

        return Response(
            {
                "script": script,
                "updated": updated_count,
            },
            status=status.HTTP_200_OK,
        )

    def _get_accessible_project(self, request_user, project_id: int):
        return Project.objects.filter(id=project_id).filter(
            Q(owner=request_user) | Q(projectmember__user=request_user),
        ).distinct().first()

    def _match_cases(self, project_id: int, interfaces: list[dict]):
        method_path_pairs: list[tuple[str, str]] = []
        for item in interfaces:
            method_value = item.get("method")
            path_value = item.get("path")
            if isinstance(method_value, str) and isinstance(path_value, str):
                method_path_pairs.append((method_value.upper(), path_value))

        queryset = ApiTestCase.objects.filter(project_id=project_id)
        if not method_path_pairs:
            return queryset

        matched_queryset = ApiTestCase.objects.none()
        for method, path in method_path_pairs:
            matched_queryset = matched_queryset | queryset.filter(method=method, path=path)
        return matched_queryset


class GenerateUiScriptView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = GenerateUiScriptRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        requirement = serializer.validated_data["requirement"]
        script = GenerateUiScriptByRequirement(requirement=requirement)

        return Response({"script": script}, status=status.HTTP_200_OK)
