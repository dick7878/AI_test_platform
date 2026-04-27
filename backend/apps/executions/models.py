from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from apps.projects.models import BaseModel, Project


class ExecutionTask(BaseModel):
    PENDING = "pending"
    RUNNING = "running"
    FINISHED = "finished"
    STATUS_CHOICES = [(PENDING, "等待"), (RUNNING, "执行中"), (FINISHED, "已完成")]

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    trigger = models.CharField(max_length=20, default="manual")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    started_at = models.DateTimeField(null=True)
    finished_at = models.DateTimeField(null=True)
    summary = models.JSONField(null=True)

    def __str__(self) -> str:
        return f"task#{self.id}:{self.status}"


class ExecutionResult(BaseModel):
    task = models.ForeignKey(ExecutionTask, on_delete=models.CASCADE, related_name="results")
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    test_case = GenericForeignKey("content_type", "object_id")

    status = models.CharField(max_length=10)
    duration = models.FloatField(null=True)
    logs = models.TextField(blank=True)
    screenshots = models.JSONField(default=list)
    request_response = models.JSONField(default=dict)
    error_message = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"result#{self.id}:{self.status}"
