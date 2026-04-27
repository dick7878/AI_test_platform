from django.urls import path

from .views import DevLoginView, DevLogoutView

urlpatterns = [
    path("dev/login/", DevLoginView.as_view(), name="dev-login"),
    path("dev/logout/", DevLogoutView.as_view(), name="dev-logout"),
]
