from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.projects.models import Project, ProjectMember

from .models import ApiEnvironment, ApiTestCase


class ApiEnvironmentTests(TestCase):
    def test_create_two_environments_for_project(self) -> None:
        owner = User.objects.create_user(username="api_env_owner", password="p@ssw0rd")
        project = Project.objects.create(name="API Project", description="", owner=owner)

        env1 = ApiEnvironment.objects.create(
            project=project,
            name="dev",
            base_url="https://dev.example.com",
            headers={"Authorization": "Bearer dev-token"},
            variables={"tenant": "dev"},
        )
        env2 = ApiEnvironment.objects.create(
            project=project,
            name="prod",
            base_url="https://prod.example.com",
            headers={"Authorization": "Bearer prod-token"},
            variables={"tenant": "prod"},
        )

        self.assertNotEqual(env1.id, env2.id)
        self.assertEqual(ApiEnvironment.objects.filter(project=project).count(), 2)


class ApiTestCaseTests(TestCase):
    def test_create_api_test_case_record(self) -> None:
        owner = User.objects.create_user(username="api_case_owner", password="p@ssw0rd")
        project = Project.objects.create(name="Case Project", description="", owner=owner)

        case = ApiTestCase.objects.create(
            project=project,
            title="Get Users Should Return 200",
            description="Validate users endpoint",
            status=ApiTestCase.DRAFT,
            method="GET",
            path="/users",
            headers={"Accept": "application/json"},
            query_params={"page": 1},
            body="",
            script="def test_get_users(api_client):\n    response = api_client.get('/users')\n    assert response.status_code == 200",
        )

        self.assertEqual(case.project_id, project.id)
        self.assertEqual(case.status, ApiTestCase.DRAFT)
        self.assertEqual(case.method, "GET")
        self.assertEqual(case.path, "/users")


class ApiTestCaseApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.owner = User.objects.create_user(username="apit_owner", password="p@ssw0rd")
        self.member = User.objects.create_user(username="apit_member", password="p@ssw0rd")
        self.outsider = User.objects.create_user(username="apit_out", password="p@ssw0rd")

        self.project = Project.objects.create(name="API Case Project", description="", owner=self.owner)
        ProjectMember.objects.create(project=self.project, user=self.member)

        self.case = ApiTestCase.objects.create(
            project=self.project,
            title="List users",
            method="GET",
            path="/users",
        )

    def test_member_can_list_cases(self) -> None:
        self.client.force_authenticate(user=self.member)

        response = self.client.get("/api/api-test-cases/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.case.id)

    def test_create_case_for_member_project(self) -> None:
        self.client.force_authenticate(user=self.member)

        response = self.client.post(
            "/api/api-test-cases/",
            {
                "project": self.project.id,
                "title": "Create by member",
                "description": "desc",
                "status": "draft",
                "method": "POST",
                "path": "/users",
                "headers": {},
                "query_params": {},
                "body": "{}",
                "script": "",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ApiTestCase.objects.filter(project=self.project).count(), 2)

    def test_filter_cases_by_project(self) -> None:
        self.client.force_authenticate(user=self.member)
        another_project = Project.objects.create(name="Another", description="", owner=self.owner)
        ApiTestCase.objects.create(project=another_project, title="Another case", method="GET", path="/x")

        response = self.client.get(f"/api/api-test-cases/?project={self.project.id}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["project"], self.project.id)

    def test_create_case_denied_for_non_member_project(self) -> None:
        self.client.force_authenticate(user=self.outsider)

        response = self.client.post(
            "/api/api-test-cases/",
            {
                "project": self.project.id,
                "title": "Should fail",
                "status": "draft",
                "method": "GET",
                "path": "/users",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_and_delete_case(self) -> None:
        self.client.force_authenticate(user=self.member)

        update_response = self.client.put(
            f"/api/api-test-cases/{self.case.id}/",
            {
                "project": self.project.id,
                "title": "Updated title",
                "description": "updated",
                "status": "ready",
                "method": "PUT",
                "path": "/users/1",
                "headers": {"X-Test": "1"},
                "query_params": {},
                "body": "{}",
                "script": "print('ok')",
            },
            format="json",
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)

        delete_response = self.client.delete(f"/api/api-test-cases/{self.case.id}/")
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
