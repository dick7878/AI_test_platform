"""确保 Django 启动时加载 Celery，以便 `@shared_task` 绑定到同一应用实例。"""

from .celery import app as celery_app

__all__ = ("celery_app",)
