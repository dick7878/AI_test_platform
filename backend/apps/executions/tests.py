from unittest.mock import patch

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.apitest.models import ApiTestCase
from apps.projects.models import Project, ProjectMember
from apps.uitest.models import UITestCase

from .models import ExecutionResult, ExecutionTask
from .tasks import BuildNotificationPayload, RunTestTask, SendExecutionNotification


class ExecutionModelsTests(TestCase):
    def test_create_execution_task_and_result(self) -> None:
        owner = User.objects.create_user(username="exec_owner", password="p@ssw0rd")
        project = Project.objects.create(name="Exec Project", description="", owner=owner)
        api_case = ApiTestCase.objects.create(project=project, title="List users", method="GET", path="/users")

        task = ExecutionTask.objects.create(
            project=project,
            trigger="manual",
            status=ExecutionTask.PENDING,
            summary={"total": 1, "passed": 0, "failed": 0, "error": 0},
        )

        case_content_type = ContentType.objects.get_for_model(ApiTestCase)
        result = ExecutionResult.objects.create(
            task=task,
            content_type=case_content_type,
            object_id=api_case.id,
            status="pass",
            duration=0.35,
            logs="ok",
            screenshots=[],
            request_response={"status_code": 200},
            error_message="",
        )

        self.assertEqual(task.project_id, project.id)
        self.assertEqual(result.task_id, task.id)
        self.assertEqual(result.test_case.id, api_case.id)


class ExecutionTaskRunnerTests(TestCase):
    def test_run_test_task_records_pytest_result(self) -> None:
        owner = User.objects.create_user(username="exec_runner_owner", password="p@ssw0rd")
        project = Project.objects.create(name="Runner Project", description="", owner=owner)
        case = ApiTestCase.objects.create(
            project=project,
            title="Runner Case",
            method="GET",
            path="/users",
            script="def test_runner_case():\n    assert True",
        )
        task = ExecutionTask.objects.create(
            project=project,
            trigger="manual",
            status=ExecutionTask.PENDING,
            summary={"submitted_case_ids": [f"api:{case.id}"]},
        )

        RunTestTask(task_id=task.id)

        task.refresh_from_db()
        result = ExecutionResult.objects.get(task=task, object_id=case.id)

        self.assertEqual(task.status, ExecutionTask.FINISHED)
        self.assertEqual(task.summary["total"], 1)
        self.assertEqual(task.summary["passed"], 1)
        self.assertEqual(result.status, "pass")

    def test_ui_case_failure_generates_screenshot_path(self) -> None:
        owner = User.objects.create_user(username="exec_ui_owner", password="p@ssw0rd")
        project = Project.objects.create(name="UI Runner Project", description="", owner=owner)
        ui_case = UITestCase.objects.create(
            project=project,
            title="Failing UI Case",
            status=UITestCase.DRAFT,
            script="def test_ui_fail(browser_page):\n    assert False",
        )
        task = ExecutionTask.objects.create(
            project=project,
            trigger="manual",
            status=ExecutionTask.PENDING,
            summary={"submitted_case_ids": [f"ui:{ui_case.id}"]},
        )

        RunTestTask(task_id=task.id)

        result = ExecutionResult.objects.get(task=task, object_id=ui_case.id)
        self.assertEqual(result.status, "fail")
        self.assertGreater(len(result.screenshots), 0)
        self.assertTrue(result.screenshots[0].startswith("/media/screenshots/"))

    def test_run_test_task_only_executes_submitted_case_ids(self) -> None:
        owner = User.objects.create_user(username="exec_selective_owner", password="p@ssw0rd")
        project = Project.objects.create(name="Selective Runner Project", description="", owner=owner)
        run_api_case = ApiTestCase.objects.create(
            project=project,
            title="Run API Case",
            method="GET",
            path="/users",
            script="def test_run_api_case():\n    assert True",
        )
        skip_api_case = ApiTestCase.objects.create(
            project=project,
            title="Skip API Case",
            method="GET",
            path="/health",
            script="def test_skip_api_case():\n    assert True",
        )
        run_ui_case = UITestCase.objects.create(
            project=project,
            title="Run UI Case",
            status=UITestCase.DRAFT,
            script="def test_run_ui_case(browser_page):\n    assert True",
        )
        skip_ui_case = UITestCase.objects.create(
            project=project,
            title="Skip UI Case",
            status=UITestCase.DRAFT,
            script="def test_skip_ui_case(browser_page):\n    assert True",
        )
        task = ExecutionTask.objects.create(
            project=project,
            trigger="manual",
            status=ExecutionTask.PENDING,
            summary={"submitted_case_ids": [f"api:{run_api_case.id}", f"ui:{run_ui_case.id}"]},
        )

        RunTestTask(task_id=task.id)

        task.refresh_from_db()
        result_pairs = set(task.results.values_list("content_type__model", "object_id"))
        self.assertEqual(task.summary["total"], 2)
        self.assertEqual(
            result_pairs,
            {
                ("apitestcase", run_api_case.id),
                ("uitestcase", run_ui_case.id),
            },
        )
        self.assertNotIn(("apitestcase", skip_api_case.id), result_pairs)
        self.assertNotIn(("uitestcase", skip_ui_case.id), result_pairs)


class ExecutionNotificationTests(TestCase):
    @patch("apps.executions.tasks.requests.post")
    def test_send_notification_when_webhook_configured(self, mocked_post) -> None:
        owner = User.objects.create_user(username="notify_owner", password="p@ssw0rd")
        project = Project.objects.create(
            name="Notify Project",
            description="",
            owner=owner,
            notification_url="https://example.com/webhook",
        )
        task = ExecutionTask.objects.create(
            project=project,
            trigger="manual",
            status=ExecutionTask.FINISHED,
            summary={"total": 1, "passed": 1, "failed": 0, "error": 0},
        )

        SendExecutionNotification(task=task)

        mocked_post.assert_called_once()

    @patch("apps.executions.tasks.requests.post")
    def test_skip_notification_when_webhook_empty(self, mocked_post) -> None:
        owner = User.objects.create_user(username="notify_owner2", password="p@ssw0rd")
        project = Project.objects.create(name="Notify Project2", description="", owner=owner, notification_url="")
        task = ExecutionTask.objects.create(project=project, trigger="manual", status=ExecutionTask.FINISHED)

        SendExecutionNotification(task=task)

        mocked_post.assert_not_called()

    def test_build_notification_payload_contains_result_link(self) -> None:
        owner = User.objects.create_user(username="notify_owner3", password="p@ssw0rd")
        project = Project.objects.create(name="Notify Project3", description="", owner=owner)
        task = ExecutionTask.objects.create(project=project, trigger="manual", status=ExecutionTask.FINISHED)

        payload = BuildNotificationPayload(task=task)

        self.assertIn("result_link", payload)
        self.assertIn(f"task_id={task.id}", payload["result_link"])


class ExecutionTaskApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.owner = User.objects.create_user(username="exec_api_owner", password="p@ssw0rd")
        self.member = User.objects.create_user(username="exec_api_member", password="p@ssw0rd")
        self.outsider = User.objects.create_user(username="exec_api_out", password="p@ssw0rd")

        self.project = Project.objects.create(name="Exec API Project", description="", owner=self.owner)
        ProjectMember.objects.create(project=self.project, user=self.member)

    @patch("apps.executions.views.run_test_task.delay")
    def test_create_execution_task_and_dispatch_celery(self, mocked_delay) -> None:
        self.client.force_authenticate(user=self.member)

        response = self.client.post(
            "/api/executions/tasks/",
            {
                "project_id": self.project.id,
                "case_ids": ["api:1", "ui:2"],
                "env_id": 3,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_task = ExecutionTask.objects.get(id=response.data["task_id"])
        self.assertEqual(created_task.status, ExecutionTask.PENDING)
        self.assertEqual(created_task.summary["env_id"], 3)
        mocked_delay.assert_called_once_with(created_task.id)

    def test_create_execution_task_denied_for_non_member(self) -> None:
        self.client.force_authenticate(user=self.outsider)

        response = self.client.post(
            "/api/executions/tasks/",
            {
                "project_id": self.project.id,
                "case_ids": ["api:1"],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_execution_task_bad_case_id_format(self) -> None:
        self.client.force_authenticate(user=self.member)

        response = self.client.post(
            "/api/executions/tasks/",
            {
                "project_id": self.project.id,
                "case_ids": ["wrong-format"],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_execution_results_success(self) -> None:
        self.client.force_authenticate(user=self.member)

        task = ExecutionTask.objects.create(
            project=self.project,
            trigger="manual",
            status=ExecutionTask.FINISHED,
            summary={"total": 1, "passed": 1, "failed": 0, "error": 0},
        )
        case = ApiTestCase.objects.create(project=self.project, title="case", method="GET", path="/users")
        content_type = ContentType.objects.get_for_model(ApiTestCase)
        ExecutionResult.objects.create(
            task=task,
            content_type=content_type,
            object_id=case.id,
            status="pass",
            duration=0.11,
            logs="ok",
            screenshots=["/media/1.png"],
            request_response={"status_code": 200},
            error_message="",
        )

        response = self.client.get(f"/api/executions/tasks/{task.id}/results/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["task_id"], task.id)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["status"], "pass")

    def test_get_execution_results_denied_for_non_member(self) -> None:
        self.client.force_authenticate(user=self.outsider)

        task = ExecutionTask.objects.create(project=self.project, trigger="manual", status=ExecutionTask.PENDING)
        response = self.client.get(f"/api/executions/tasks/{task.id}/results/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_execution_results_not_found(self) -> None:
        self.client.force_authenticate(user=self.member)

        response = self.client.get("/api/executions/tasks/999999/results/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
