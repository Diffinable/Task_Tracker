from django.shortcuts import render
from rest_framework import generics, permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import User, Task, UserTask
from .serializers import UserSerializer, TaskSerializer, AddExecutorSerializer
from .permissions import IsTaskOwner

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
        if self.action in ['update', 'partial_update', 'destroy', 'add_executor']:
            permission_classes = [permissions.IsAuthenticated, IsTaskOwner]
        else:
            permission_classes = [permissions.IsAuthenticated]

        return [permission() for permission in permission_classes] 
    
    def get_serializer_class(self):
        if self.action == "add_executor":
            return AddExecutorSerializer
        return TaskSerializer
    
    @action(detail=True, methods=['post'], name='Add Executor')
    def add_executor(self, request, pk=None):
        task = self.get_object()
        serializer = AddExecutorSerializer(data=request.data)

        if serializer.is_valid():
            user_id = serializer.validated_data['user_id']
            try:
                user_to_add = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

            _, created = UserTask.objects.get_or_create(
                user=user_to_add,
                task=task,
                defaults={'role': UserTask.Role.EXECUTOR}
            )

            if not created:
                return Response({'error': 'User is already in this task'}, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({'status': 'executor added'}, status=status.HTTP_200_OK)

        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)