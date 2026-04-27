from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.projects.models import Project, ProjectMember

from .models import UIEnvironment, UITestCase


class UITestModelTests(TestCase):
    def test_create_ui_environment_and_case(self) -> None:
        owner = User.objects.create_user(username="ui_owner", password="p@ssw0rd")
        project = Project.objects.create(name="UI Project", description="", owner=owner)

        environment = UIEnvironment.objects.create(
            project=project,
            name="staging",
            target_url="https://staging.example.com",
            browser="chromium",
            viewport="1280x720",
            implicit_wait=5.0,
        )
        ui_case = UITestCase.objects.create(
            project=project,
            title="Login flow",
            description="Validate login redirect",
            status=UITestCase.DRAFT,
            script="def test_login(page):\n    assert True",
            elements_snapshot={"loginButton": "button[type=submit]"},
        )

        self.assertEqual(environment.project_id, project.id)
        self.assertEqual(ui_case.project_id, project.id)
        self.assertEqual(UITestCase.objects.filter(project=project).count(), 1)


class UITestCaseApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.owner = User.objects.create_user(username="ui_api_owner", password="p@ssw0rd")
        self.member = User.objects.create_user(username="ui_api_member", password="p@ssw0rd")
        self.outsider = User.objects.create_user(username="ui_api_out", password="p@ssw0rd")

        self.project = Project.objects.create(name="UI API Project", description="", owner=self.owner)
        ProjectMember.objects.create(project=self.project, user=self.member)

        self.case = UITestCase.objects.create(
            project=self.project,
            title="Open Home",
            description="check home",
            status=UITestCase.DRAFT,
            script="",
            elements_snapshot={"home": "#home"},
        )

    def test_member_can_list_cases(self) -> None:
        self.client.force_authenticate(user=self.member)

        response = self.client.get("/api/ui-test-cases/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.case.id)

    def test_member_can_create_case(self) -> None:
        self.client.force_authenticate(user=self.member)

        response = self.client.post(
            "/api/ui-test-cases/",
            {
                "project": self.project.id,
                "title": "Login UI",
                "description": "login",
                "status": "draft",
                "script": "def test_login(page):\n    assert True",
                "elements_snapshot": {"submit": "button[type=submit]"},
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UITestCase.objects.filter(project=self.project).count(), 2)

    def test_filter_by_project(self) -> None:
        self.client.force_authenticate(user=self.member)
        another_project = Project.objects.create(name="UI API Project 2", description="", owner=self.owner)
        UITestCase.objects.create(project=another_project, title="Another", status=UITestCase.DRAFT)

        response = self.client.get(f"/api/ui-test-cases/?project={self.project.id}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["project"], self.project.id)

    def test_non_member_cannot_create_case(self) -> None:
        self.client.force_authenticate(user=self.outsider)

        response = self.client.post(
            "/api/ui-test-cases/",
            {
                "project": self.project.id,
                "title": "Should fail",
                "status": "draft",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_member_can_update_and_delete_case(self) -> None:
        self.client.force_authenticate(user=self.member)

        update_response = self.client.put(
            f"/api/ui-test-cases/{self.case.id}/",
            {
                "project": self.project.id,
                "title": "Open Home Updated",
                "description": "updated",
                "status": "ready",
                "script": "def test_home(page):\n    assert True",
                "elements_snapshot": {"home": "#home-new"},
            },
            format="json",
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)

        delete_response = self.client.delete(f"/api/ui-test-cases/{self.case.id}/")
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
