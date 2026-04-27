from rest_framework.routers import DefaultRouter

from .views import ApiTestCaseViewSet

router = DefaultRouter()
router.register("api-test-cases", ApiTestCaseViewSet, basename="api-test-case")

urlpatterns = router.urls
