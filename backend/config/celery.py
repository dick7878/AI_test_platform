"""
Celery 应用入口（tasks.md T002）。

Worker 启动：`celery -A config worker -l info`（需 Redis 与 `CELERY_BROKER_URL` 可达）。
"""

from __future__ import annotations

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("aits")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
