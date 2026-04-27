from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.apitest.models import ApiTestCase
from apps.projects.models import Project, ProjectMember

from .services import (
    BuildApiGenerationPrompt,
    BuildUiGenerationPrompt,
    GenerateApiScriptByInterfaces,
    GenerateUiScriptByRequirement,
    call_llm,
)


class AiServicesTests(TestCase):
    @patch("apps.ai.services._invoke_model")
    def test_call_llm_returns_model_output(self, mocked_invoke) -> None:
        mocked_invoke.return_value = "print('hello world from llm')"

        result = call_llm("返回 hello world Python")

        self.assertIn("hello world", result)

    @patch("apps.ai.services._invoke_model")
    def test_call_llm_fallback_when_model_failed(self, mocked_invoke) -> None:
        mocked_invoke.side_effect = ValueError("model failed")

        result = call_llm("返回 hello world Python")

        self.assertIn("def test_", result)

    def test_build_api_generation_prompt(self) -> None:
        prompt = BuildApiGenerationPrompt('[{"method": "GET", "path": "/users"}]')

        self.assertIn("接口列表 JSON", prompt)
        self.assertIn("/users", prompt)

    def test_build_ui_generation_prompt(self) -> None:
        prompt = BuildUiGenerationPrompt("打开登录页并登录")

        self.assertIn("用户需求", prompt)
        self.assertIn("登录", prompt)

    @patch("apps.ai.services.call_llm")
    def test_generate_api_script_by_interfaces(self, mocked_call_llm) -> None:
        mocked_call_llm.return_value = "def test_users():\n    assert True"

        result = GenerateApiScriptByInterfaces([
            {"method": "GET", "path": "/users", "summary": "list users"},
        ])

        self.assertIn("def test_users", result)

    @patch("apps.ai.services.call_llm")
    def test_generate_ui_script_by_requirement(self, mocked_call_llm) -> None:
        mocked_call_llm.return_value = "def test_ui(page):\n    assert True"

        result = GenerateUiScriptByRequirement("打开登录页并登录")

        self.assertIn("def test_ui", result)


class GenerateApiScriptApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.owner = User.objects.create_user(username="ai_owner", password="p@ssw0rd")
        self.member = User.objects.create_user(username="ai_member", password="p@ssw0rd")
        self.outsider = User.objects.create_user(username="ai_out", password="p@ssw0rd")

        self.project = Project.objects.create(name="AI Project", description="", owner=self.owner)
        ProjectMember.objects.create(project=self.project, user=self.member)
        self.case = ApiTestCase.objects.create(
            project=self.project,
            title="List users",
            method="GET",
            path="/users",
            script="",
        )

    @patch("apps.ai.views.GenerateApiScriptByInterfaces")
    def test_generate_script_and_save_case(self, mocked_generate) -> None:
        mocked_generate.return_value = "def test_users():\n    assert True"
        self.client.force_authenticate(user=self.member)

        response = self.client.post(
            "/api/ai/generate-api-script/",
            {
                "project_id": self.project.id,
                "interfaces": [{"method": "GET", "path": "/users", "summary": "list users"}],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["updated"], 1)
        self.case.refresh_from_db()
        self.assertIn("def test_users", self.case.script)

    @patch("apps.ai.views.GenerateApiScriptByInterfaces")
    def test_generate_script_denied_for_non_member(self, mocked_generate) -> None:
        mocked_generate.return_value = "def test_users():\n    assert True"
        self.client.force_authenticate(user=self.outsider)

        response = self.client.post(
            "/api/ai/generate-api-script/",
            {
                "project_id": self.project.id,
                "interfaces": [{"method": "GET", "path": "/users"}],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_generate_script_bad_payload(self) -> None:
        self.client.force_authenticate(user=self.member)

        response = self.client.post(
            "/api/ai/generate-api-script/",
            {
                "project_id": self.project.id,
                "interfaces": [],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class GenerateUiScriptApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(username="ui_script_user", password="p@ssw0rd")

    @patch("apps.ai.views.GenerateUiScriptByRequirement")
    def test_generate_ui_script_success(self, mocked_generate) -> None:
        mocked_generate.return_value = "def test_login(page):\n    assert page is not None"
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/api/ai/generate-ui-script/",
            {"requirement": "打开登录页，用admin/admin登录，验证跳转"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("def test_login", response.data["script"])

    def test_generate_ui_script_bad_payload(self) -> None:
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/api/ai/generate-ui-script/",
            {"requirement": ""},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
