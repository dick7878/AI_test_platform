from rest_framework.routers import DefaultRouter

from .views import UITestCaseViewSet

router = DefaultRouter()
router.register("ui-test-cases", UITestCaseViewSet, basename="ui-test-case")

urlpatterns = router.urls
