from django.urls import path, include
from rest_framework_nested import routers 
from .views import RegisterView, TaskViewSet, UserTaskViewSet, BranchesTaskViewSet, ChangePasswordView

router = routers.SimpleRouter()
router.register(r'tasks', TaskViewSet, basename='task')
users_task_router = routers.NestedSimpleRouter(router, r'tasks', lookup='task')
users_task_router.register(r'users', UserTaskViewSet, basename='task-users')
branches_task_router = routers.NestedSimpleRouter(router, r"tasks", lookup='task')
branches_task_router.register(r"branches", BranchesTaskViewSet, basename="task-branches")

urlpatterns = [
    path('', include(router.urls)),
    path('', include(users_task_router.urls)),
    path('', include(branches_task_router.urls)),    
    path("register/", RegisterView.as_view(), name='register'),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
]