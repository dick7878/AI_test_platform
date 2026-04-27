from django.urls import path

from .views import CreateExecutionTaskView, ExecutionTaskResultsView

urlpatterns = [
    path("executions/tasks/", CreateExecutionTaskView.as_view(), name="create-execution-task"),
    path("executions/tasks/<int:task_id>/results/", ExecutionTaskResultsView.as_view(), name="execution-task-results"),
]
