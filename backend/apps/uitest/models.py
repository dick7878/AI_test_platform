from django.db import models

from apps.projects.models import BaseModel, Project


class UIEnvironment(BaseModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="ui_envs")
    name = models.CharField(max_length=100)
    target_url = models.URLField()
    browser = models.CharField(max_length=20, default="chromium")
    viewport = models.CharField(max_length=20, default="1280x720")
    implicit_wait = models.FloatField(default=5.0)

    def __str__(self) -> str:
        return f"{self.project.name}:{self.name}"


class UITestCase(BaseModel):
    DRAFT = "draft"
    READY = "ready"
    STATUS_CHOICES = [(DRAFT, "草稿"), (READY, "就绪")]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="ui_cases")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=DRAFT)

    script = models.TextField(blank=True)
    elements_snapshot = models.JSONField(null=True, blank=True)

    last_run_status = models.CharField(max_length=10, null=True)
    last_run_at = models.DateTimeField(null=True)

    def __str__(self) -> str:
        return f"{self.project.name}:{self.title}"
