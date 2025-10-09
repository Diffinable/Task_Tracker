from django.shortcuts import render
from rest_framework import generics, permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import User, Task, UserTask
from .serializers import UserSerializer, TaskSerializer, ManageParticipantSerializer, LogWorkTimeSerializer, UserTaskSerializer
from .permissions import IsTaskOwner, IsAssignedToTask, IsSelf

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserSerializer

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    base_permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        task = serializer.save()
        UserTask.objects.create(
            user=self.request.user,
            task=task,
            role=UserTask.Role.OWNER
        )

    def get_permissions(self):
        permission_classes = self.base_permission_classes
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes.append(IsTaskOwner)
        return [permission() for permission in permission_classes] 
    
class UserTaskViewSet(viewsets.ModelViewSet):
    serializer_class = UserTaskSerializer
    base_permission_classes = [permissions.IsAuthenticated]


    def get_queryset(self):
        return UserTask.objects.filter(task_id=self.kwargs['task_pk'])
    
    def get_permissions(self):
        permission_classes = self.base_permission_classes

        if self.action == "log_time":
            permission_classes.append(IsSelf)
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        if self.action == "log_time":
            return LogWorkTimeSerializer
        return UserTaskSerializer
    
    def perform_create(self, serializer):
        serializer.save(task_id=self.kwargs['task_pk'])

    @action(detail=True, methods=["post"], name="Log work time")
    def log_time(self, request, task_pk=None, pk=None):
        user_task = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            hours_to_add = serializer.validated_data['hours']
            user_task = UserTask.objects.get(user=request.user, task=task)

            current_work_time = user_task.work_time or 0
            user_task.work_time = current_work_time + hours_to_add
            user_task.save()

            return Response(
                {'status': 'time logged', 'total_work_time': user_task.work_time},
                status=status.HTTP_200_OK
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

