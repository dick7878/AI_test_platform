from django.db.models import Q
from rest_framework import permissions, viewsets
from rest_framework.exceptions import PermissionDenied

from apps.projects.models import Project

from .models import UITestCase
from .serializers import UITestCaseSerializer


class UITestCaseViewSet(viewsets.ModelViewSet):
    serializer_class = UITestCaseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def _get_accessible_projects(self):
        user = self.request.user
        return Project.objects.filter(Q(owner=user) | Q(projectmember__user=user)).distinct()

    def get_queryset(self):
        queryset = UITestCase.objects.filter(project__in=self._get_accessible_projects())
        project_id = self.request.query_params.get("project")
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset

    def perform_create(self, serializer) -> None:
        project = serializer.validated_data["project"]
        if not self._get_accessible_projects().filter(id=project.id).exists():
            raise PermissionDenied("You do not have permission to use this project.")
        serializer.save()

    def perform_update(self, serializer) -> None:
        project = serializer.validated_data.get("project", serializer.instance.project)
        if not self._get_accessible_projects().filter(id=project.id).exists():
            raise PermissionDenied("You do not have permission to use this project.")
        serializer.save()
