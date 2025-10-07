from rest_framework import permissions
from .models import UserTask

class IsTaskOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return UserTask.objects.filter(
            user=request.user,
            task=obj,
            role=UserTask.Role.OWNER
        ).exists()
    
class IsAssignedToTask(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return UserTask.objects.filter(user=request.user, task=obj).exists()