from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegisterView, TaskViewSet, UserTaskViewSet

router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'tasks/(P<task_pk>[^/.]+)/users', UserTaskViewSet, basename='task-users')

urlpatterns = [
    path('', include(router.urls)),
    path("register/", RegisterView.as_view(), name='register'),
]