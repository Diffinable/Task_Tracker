from django.shortcuts import render
from rest_framework import generics, permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.db import transaction
from .models import User, Task, UserTask, BranchesTask
from .serializers import UserSerializer, TaskSerializer, LogWorkTimeSerializer, UserTaskSerializer, BranchesTaskSerializer, ChangePasswordSerializer
from .permissions import IsTaskOwner, IsSelf, IsParticipantOfTask
from .services import GitHubService

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserSerializer

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    base_permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        permission_classes = self.base_permission_classes[:]
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes.append(IsTaskOwner)
        elif self.action == 'retrieve':
            permission_classes.append(IsParticipantOfTask)
        return [permission() for permission in permission_classes] 
    
class BranchesTaskViewSet(viewsets.ModelViewSet):
    serializer_class = BranchesTaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsParticipantOfTask]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return BranchesTask.objects.none()
        return BranchesTask.objects.filter(task_id=self.kwargs['task_pk'])
    
    def perform_destroy(self, instance):
        branch_name = instance.name
        gh_service = GitHubService()
        gh_service.delete_branch(branch_name)
        instance.delete()

class UserTaskViewSet(viewsets.ModelViewSet):
    serializer_class = UserTaskSerializer
    base_permission_classes = [permissions.IsAuthenticated]


    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return UserTask.objects.none()
        return UserTask.objects.filter(task_id=self.kwargs['task_pk'])
    
    def get_permissions(self):
        permission_classes = self.base_permission_classes[:]

        if self.action == "log_time":
            permission_classes.append(IsSelf)
        elif self.action in ['list', 'retrieve']:
            permission_classes.append(IsParticipantOfTask)
        else:
            permission_classes.append(IsTaskOwner)
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
        serializer = self.get_serializer(instance=user_task, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )
    
class ChangePasswordView(generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = User.objects.all()

    def get_object(self, queryset=None):
        return self.request.user

    def put(self, request, *args, **kwargs):
        user = self.request.user
        serializer = self.get_serializer(data=self.request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"status": "password set successfully"}, status=status.HTTP_200_OK)

