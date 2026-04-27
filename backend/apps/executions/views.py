from django.db.models import Q
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.projects.models import Project

from .models import ExecutionTask
from .serializers import CreateExecutionTaskRequestSerializer
from .tasks import run_test_task


class CreateExecutionTaskView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = CreateExecutionTaskRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        project_id = serializer.validated_data["project_id"]
        case_ids = serializer.validated_data["case_ids"]
        env_id = serializer.validated_data.get("env_id")

        project = self._get_accessible_project(user=request.user, project_id=project_id)
        if project is None:
            return Response({"detail": "Project not found."}, status=status.HTTP_404_NOT_FOUND)

        execution_task = ExecutionTask.objects.create(
            project=project,
            trigger="manual",
            status=ExecutionTask.PENDING,
            summary={
                "submitted_case_ids": case_ids,
                "env_id": env_id,
            },
        )

        run_test_task.delay(execution_task.id)

        return Response(
            {
                "task_id": execution_task.id,
                "status": execution_task.status,
            },
            status=status.HTTP_201_CREATED,
        )

    def _get_accessible_project(self, user, project_id: int):
        return Project.objects.filter(id=project_id).filter(
            Q(owner=user) | Q(projectmember__user=user),
        ).distinct().first()


class ExecutionTaskResultsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, task_id: int, *args, **kwargs):
        task = (
            ExecutionTask.objects.select_related("project")
            .prefetch_related("results__content_type")
            .filter(id=task_id)
            .first()
        )
        if task is None:
            return Response({"detail": "Task not found."}, status=status.HTTP_404_NOT_FOUND)

        if not self._has_project_access(user=request.user, project_id=task.project_id):
            return Response({"detail": "Task not found."}, status=status.HTTP_404_NOT_FOUND)

        result_items: list[dict] = []
        for item in task.results.select_related("content_type").all().order_by("id"):
            result_items.append(
                {
                    "id": item.id,
                    "content_type": item.content_type.model,
                    "object_id": item.object_id,
                    "status": item.status,
                    "duration": item.duration,
                    "logs": item.logs,
                    "screenshots": item.screenshots,
                    "request_response": item.request_response,
                    "error_message": item.error_message,
                    "created_at": item.created_at,
                }
            )

        return Response(
            {
                "task_id": task.id,
                "status": task.status,
                "summary": task.summary,
                "results": result_items,
            },
            status=status.HTTP_200_OK,
        )

    def _has_project_access(self, user, project_id: int) -> bool:
        return (
            Project.objects.filter(id=project_id)
            .filter(Q(owner=user) | Q(projectmember__user=user))
            .distinct()
            .exists()
        )
