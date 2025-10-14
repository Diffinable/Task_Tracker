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
    def has_permission(self, request, view):
        task_pk = view.kwargs.get('task_pk')
        if not task_pk:
            task_pk = view.kwargs.get('pk')
            if not task_pk:
                return True
            
        
        try:
            task = Task.objects.get(pk=task_pk)
        except Task.DoesNotExist:
            return False
        
        return UserTask.objects.filter(user=request.user, task=task).exists()
    
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Task):
            task = obj
        elif hasattr(obj, 'task'):
            task = obj.task
        else: 
            return False
        
        return UserTask.objects.filter(user=request.user, task=task).exists()
    
class IsSelf(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
