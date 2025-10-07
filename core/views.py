from django.shortcuts import render
from rest_framework import generics, permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import User, Task, UserTask
from .serializers import UserSerializer, TaskSerializer, ManageParticipantSerializer, LogWorkTimeSerializer
from .permissions import IsTaskOwner, IsAssignedToTask

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserSerializer

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    def perform_create(self, serializer):
        task = serializer.save()
        UserTask.objects.create(
            user=self.request.user,
            task=task,
            role=UserTask.Role.OWNER
        )

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy', 'manage_participant']:
            permission_classes = [permissions.IsAuthenticated, IsTaskOwner]
        elif self.action in ['log_time']:
            permission_classes = [permissions.IsAuthenticated, IsAssignedToTask]
        else:
            permission_classes = [permissions.IsAuthenticated]

        return [permission() for permission in permission_classes] 
    
    def get_serializer_class(self):
        if self.action == "manage_participant":
            return ManageParticipantSerializer
        elif self.action == "log_time":
            return LogWorkTimeSerializer
        return TaskSerializer
    
    @action(detail=True, methods=['post'], name='Manage participant')
    def manage_participant(self, request, pk=None):
        task = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            user_id = serializer.validated_data['user_id']
            new_role = serializer.validated_data['role']
            try:
                user_to_manage = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

            user_task, created = UserTask.objects.update_or_create(
                user=user_to_manage,
                task=task,
                defaults={'role': new_role}
            )
            if created:
                message = "Participant created"
            else:
                message = "Participant role updated"

            
            return Response({'status': message, 'user_d': user_id, 'new_role': new_role}, status=status.HTTP_200_OK)

        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=True, methods=["post"], name="Log work time")
    def log_time(self, request, pk=None):
        task = self.get_object()
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