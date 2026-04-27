"""URL configuration for config project (T001：根路径欢迎页便于 Docker 验收)."""

from django.contrib import admin
from django.http import HttpRequest, HttpResponse
from django.urls import include, path


def Welcome(_request: HttpRequest) -> HttpResponse:
    """根路径欢迎页，满足 `docker-compose up` 后在浏览器可验收。"""
    body = (
        "<!DOCTYPE html><html lang='zh-CN'><head><meta charset='utf-8'/>"
        "<title>AITS Backend</title></head><body>"
        "<h1>AITS 后端已就绪</h1>"
        "<p>Django 运行正常。请继续按 tasks.md 执行后续任务。</p>"
        "</body></html>"
    )
    return HttpResponse(body, content_type="text/html; charset=utf-8")


urlpatterns = [
    path("", Welcome, name="welcome"),
    path("admin/", admin.site.urls),
    path("api/", include("apps.users.urls")),
    path("api/", include("apps.projects.urls")),
    path("api/", include("apps.apitest.urls")),
    path("api/", include("apps.uitest.urls")),
    path("api/", include("apps.executions.urls")),
    path("api/ai/", include("apps.ai.urls")),
]
