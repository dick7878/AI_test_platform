from django.db import models

from apps.projects.models import BaseModel, Project


class ApiEnvironment(BaseModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="api_envs")
    name = models.CharField(max_length=100)
    base_url = models.URLField()
    headers = models.JSONField(default=dict, blank=True)
    variables = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return f"{self.project.name}:{self.name}"


class ApiTestCase(BaseModel):
    DRAFT = "draft"
    READY = "ready"
    STATUS_CHOICES = [(DRAFT, "草稿"), (READY, "就绪")]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="api_cases")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=DRAFT)

    method = models.CharField(max_length=10, default="GET")
    path = models.CharField(max_length=500)
    headers = models.JSONField(default=dict, blank=True)
    query_params = models.JSONField(default=dict, blank=True)
    body = models.TextField(blank=True)

    script = models.TextField(blank=True)

    last_run_status = models.CharField(max_length=10, null=True)
    last_run_at = models.DateTimeField(null=True)

    def __str__(self) -> str:
        return f"{self.project.name}:{self.title}"
