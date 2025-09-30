from django.shortcuts import render
from rest_framework import generics, permissions, viewsets
from .models import User, Task, UserTask
from .serializers import UserSerializer, TaskSerializer

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