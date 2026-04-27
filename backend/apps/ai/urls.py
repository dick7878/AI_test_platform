from django.urls import path

from .views import GenerateApiScriptView, GenerateUiScriptView

urlpatterns = [
    path("generate-api-script/", GenerateApiScriptView.as_view(), name="generate-api-script"),
    path("generate-ui-script/", GenerateUiScriptView.as_view(), name="generate-ui-script"),
]
