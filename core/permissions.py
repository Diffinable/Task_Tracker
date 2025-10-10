from rest_framework import permissions
from .models import UserTask, Task

class IsTaskOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return UserTask.objects.filter(
            user=request.user,
            task=obj,
            role=UserTask.Role.OWNER
        ).exists()
    
class IsParticipantOfTask(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        task_pk = view.kwargs.get('task_pk')
        if not task_pk:
            return False
        
        try:
            task = Task.objects.get(pk=task_pk)
        except Task.DoesNotExist:
            return False
        
        return UserTask.objects.filter(user=request.user, task=obj).exists()
    
class IsSelf(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
