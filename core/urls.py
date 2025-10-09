from django.urls import path, include
from rest_framework_nested import routers 
from .views import RegisterView, TaskViewSet, UserTaskViewSet

router = routers.SimpleRouter()
router.register(r'tasks', TaskViewSet, basename='task')
task_router = routers.NestedSimpleRouter(router, r'tasks', lookup='task')
task_router.register(r'users', UserTaskViewSet, basename='task-users')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(task_router.urls)),
    path("register/", RegisterView.as_view(), name='register'),
]