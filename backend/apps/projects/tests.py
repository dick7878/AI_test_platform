from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.apitest.models import ApiTestCase

from .models import Project, ProjectMember


class ProjectModelTests(TestCase):
    def test_create_project_and_member(self) -> None:
        owner = User.objects.create_user(username="owner", password="p@ssw0rd")
        member = User.objects.create_user(username="member", password="p@ssw0rd")

        project = Project.objects.create(name="Demo", description="desc", owner=owner)
        project_member = ProjectMember.objects.create(project=project, user=member)

        self.assertEqual(project.name, "Demo")
        self.assertEqual(project_member.project_id, project.id)
        self.assertEqual(project_member.user_id, member.id)

    def test_project_member_unique_constraint(self) -> None:
        owner = User.objects.create_user(username="owner2", password="p@ssw0rd")
        member = User.objects.create_user(username="member2", password="p@ssw0rd")

        project = Project.objects.create(name="Demo2", description="", owner=owner)
        ProjectMember.objects.create(project=project, user=member)

        with self.assertRaises(IntegrityError):
            ProjectMember.objects.create(project=project, user=member)


class ProjectApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.owner = User.objects.create_user(username="api_owner", password="p@ssw0rd")
        self.member = User.objects.create_user(username="api_member", password="p@ssw0rd")
        self.outsider = User.objects.create_user(username="api_out", password="p@ssw0rd")

        self.project = Project.objects.create(name="API Demo", description="d", owner=self.owner)
        ProjectMember.objects.create(project=self.project, user=self.member)

    def test_create_project_auto_set_owner(self) -> None:
        self.client.force_authenticate(user=self.member)

        response = self.client.post(
            "/api/projects/",
            {"name": "New Project", "description": "from api", "owner": self.owner.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_project = Project.objects.get(id=response.data["id"])
        self.assertEqual(created_project.owner_id, self.member.id)

    def test_member_can_list_project(self) -> None:
        self.client.force_authenticate(user=self.member)

        response = self.client.get("/api/projects/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.project.id)

    def test_non_member_cannot_access_project_detail(self) -> None:
        self.client.force_authenticate(user=self.outsider)

        response = self.client.get(f"/api/projects/{self.project.id}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_import_swagger_json_creates_api_cases(self) -> None:
        self.client.force_authenticate(user=self.member)
        payload = {
            "openapi": "3.0.0",
            "paths": {
                "/users": {
                    "get": {"summary": "List users", "description": "get users"},
                    "post": {"summary": "Create user", "description": "create user"},
                }
            },
        }

        response = self.client.post(
            f"/api/projects/{self.project.id}/import-swagger/",
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["created"], 2)
        self.assertEqual(ApiTestCase.objects.filter(project=self.project).count(), 2)
        self.assertTrue(
            ApiTestCase.objects.filter(project=self.project, status=ApiTestCase.DRAFT, script="").exists(),
        )

    def test_import_swagger_yaml_creates_api_cases(self) -> None:
        self.client.force_authenticate(user=self.member)
        yaml_content = """
openapi: 3.0.0
paths:
  /health:
    get:
      summary: health check
      description: check service status
"""
        upload = SimpleUploadedFile("swagger.yaml", yaml_content.encode("utf-8"), content_type="text/yaml")

        response = self.client.post(
            f"/api/projects/{self.project.id}/import-swagger/",
            {"file": upload},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["created"], 1)
        self.assertEqual(ApiTestCase.objects.filter(project=self.project, path="/health").count(), 1)
