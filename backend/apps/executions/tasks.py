from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import textwrap
import time
from pathlib import Path

import requests
from celery import shared_task
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils import timezone

from apps.apitest.models import ApiTestCase
from apps.uitest.models import UITestCase

from .models import ExecutionResult, ExecutionTask

_SCREENSHOT_MARKER_PREFIX = "AITS_SCREENSHOT_PATH::"


def BuildConftestContent() -> str:
    return textwrap.dedent(
        """
        from __future__ import annotations

        import os
        import time
        from pathlib import Path

        import pytest
        import requests


        class ApiClient:
            def __init__(self) -> None:
                self._session = requests.Session()
                self.base_url = ""

            def get(self, path: str, **kwargs):
                return self._session.get(f"{self.base_url}{path}", timeout=10, **kwargs)

            def post(self, path: str, **kwargs):
                return self._session.post(f"{self.base_url}{path}", timeout=10, **kwargs)


        @pytest.fixture
        def api_client() -> ApiClient:
            return ApiClient()


        @pytest.fixture
        def browser_page():
            # T021 MVP: provide dummy object for UI scripts; screenshot generation by pytest hook.
            class DummyPage:
                pass

            return DummyPage()


        @pytest.hookimpl(hookwrapper=True)
        def pytest_runtest_makereport(item, call):
            outcome = yield
            report = outcome.get_result()
            if report.when != "call" or report.passed:
                return

            screenshot_dir = Path(os.environ.get("AITS_SCREENSHOT_DIR", ""))
            if not str(screenshot_dir):
                return

            screenshot_dir.mkdir(parents=True, exist_ok=True)
            safe_name = item.name.replace("/", "_").replace(chr(92), "_")
            filename = f"{safe_name}_{int(time.time() * 1000)}.png"
            file_path = screenshot_dir / filename

            # Placeholder screenshot for MVP runner; real browser screenshot in T021+.
            file_path.write_bytes(b"AITS_SCREENSHOT_PLACEHOLDER")

            media_url = os.environ.get("AITS_MEDIA_URL", "/media/").rstrip("/")
            relative_path = f"{media_url}/screenshots/{filename}"
            print(f"AITS_SCREENSHOT_PATH::{relative_path}")
        """
    ).strip() + "\n"


def BuildCaseTestFileContent(script: str) -> str:
    user_script = script.strip() or "def test_case_placeholder():\n    assert True"
    return f"{user_script}\n"


def ParseScreenshotPathsFromLogs(logs: str) -> list[str]:
    pattern = re.compile(rf"{_SCREENSHOT_MARKER_PREFIX}([^\r\n]+)")
    return [item.strip() for item in pattern.findall(logs) if item.strip()]


def RunSinglePytest(test_file_path: Path, screenshot_dir: Path, media_url: str) -> tuple[str, float, str, list[str]]:
    start_time = time.time()
    env = os.environ.copy()
    env["AITS_SCREENSHOT_DIR"] = str(screenshot_dir)
    env["AITS_MEDIA_URL"] = media_url

    process = subprocess.run(
        [sys.executable, "-m", "pytest", test_file_path.name, "-q"],
        check=False,
        capture_output=True,
        text=True,
        cwd=str(test_file_path.parent),
        env=env,
    )
    duration = time.time() - start_time
    logs = f"STDOUT:\n{process.stdout}\n\nSTDERR:\n{process.stderr}".strip()
    screenshot_paths = ParseScreenshotPathsFromLogs(logs=logs)

    if process.returncode == 0:
        return "pass", duration, logs, screenshot_paths
    if process.returncode == 1:
        return "fail", duration, logs, screenshot_paths
    return "error", duration, logs, screenshot_paths


def BuildNotificationPayload(task: ExecutionTask) -> dict:
    summary = task.summary or {}
    result_link = f"/projects/{task.project_id}/executions?task_id={task.id}"
    return {
        "msg_type": "text",
        "task_id": task.id,
        "project_id": task.project_id,
        "status": task.status,
        "summary": summary,
        "result_link": result_link,
        "text": {
            "content": (
                f"AITS执行完成\n"
                f"任务ID: {task.id}\n"
                f"项目ID: {task.project_id}\n"
                f"状态: {task.status}\n"
                f"摘要: {summary}\n"
                f"结果链接: {result_link}"
            )
        },
    }


def SendExecutionNotification(task: ExecutionTask) -> None:
    webhook_url = (task.project.notification_url or "").strip()
    if not webhook_url:
        return

    payload = BuildNotificationPayload(task=task)
    try:
        requests.post(webhook_url, json=payload, timeout=10)
    except requests.RequestException:
        # Notification failure should not break execution main flow.
        return


def RunTestTask(task_id: int) -> None:
    task = ExecutionTask.objects.select_related("project").get(id=task_id)
    task.status = ExecutionTask.RUNNING
    task.started_at = timezone.now()
    task.save(update_fields=["status", "started_at", "updated_at"])

    api_content_type = ContentType.objects.get_for_model(ApiTestCase)
    ui_content_type = ContentType.objects.get_for_model(UITestCase)

    cases_to_run: list[tuple[int, str, int, str]] = []
    for api_case in ApiTestCase.objects.filter(project=task.project).exclude(script=""):
        cases_to_run.append((api_case.id, api_case.script, api_content_type.id, "api"))
    for ui_case in UITestCase.objects.filter(project=task.project).exclude(script=""):
        cases_to_run.append((ui_case.id, ui_case.script, ui_content_type.id, "ui"))

    total = 0
    passed = 0
    failed = 0
    errored = 0

    media_root = Path(settings.MEDIA_ROOT)
    screenshot_root = media_root / "screenshots"
    screenshot_root.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="aits_exec_") as tmp_dir:
        temp_path = Path(tmp_dir)
        (temp_path / "conftest.py").write_text(BuildConftestContent(), encoding="utf-8")

        for case_id, script, content_type_id, _case_type in cases_to_run:
            total += 1
            test_file = temp_path / f"test_case_{content_type_id}_{case_id}.py"
            test_file.write_text(BuildCaseTestFileContent(script=script), encoding="utf-8")
            status_value, duration, logs, screenshots = RunSinglePytest(
                test_file_path=test_file,
                screenshot_dir=screenshot_root,
                media_url=settings.MEDIA_URL,
            )

            if status_value == "pass":
                passed += 1
            elif status_value == "fail":
                failed += 1
            else:
                errored += 1

            ExecutionResult.objects.create(
                task=task,
                content_type_id=content_type_id,
                object_id=case_id,
                status=status_value,
                duration=duration,
                logs=logs,
                screenshots=screenshots,
                request_response={},
                error_message="" if status_value == "pass" else "pytest execution failed",
            )

    with transaction.atomic():
        task.status = ExecutionTask.FINISHED
        task.finished_at = timezone.now()
        task.summary = {
            "total": total,
            "passed": passed,
            "failed": failed,
            "error": errored,
        }
        task.save(update_fields=["status", "finished_at", "summary", "updated_at"])

    SendExecutionNotification(task=task)


@shared_task(name="executions.run_test_task")
def run_test_task(task_id: int) -> None:
    RunTestTask(task_id=task_id)
