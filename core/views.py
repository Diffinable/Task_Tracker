from django.shortcuts import render
from rest_framework import generics, permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.db import transaction
from .models import User, Task, UserTask, BranchesTask
from .serializers import UserSerializer, TaskSerializer, LogWorkTimeSerializer, UserTaskSerializer, BranchesTaskSerializer, ChangePasswordSerializer
from .permissions import IsTaskOwner, IsSelf, IsParticipantOfTask

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
    
    def perform_create(self, serializer):
        from github import Github, GithubException
        from django.conf import settings

        task_id = self.kwargs['task_pk']
        branch_name = serializer.validated_data.get('name')
        try:
            g = Github(settings.GITHUB_ACCESS_TOKEN)
            repo = g.get_repo(settings.GITHUB_REPO_NAME)
            try:
                source_branch = repo.get_branch('main')
                source_sha = source_branch.commit.sha
                repo.create_git_ref(f"refs/heads/{branch_name}", sha=source_sha)
                print(f"Created GitHub branch: {branch_name}")
            except GithubException as e:
                if e.status == 422 and "already exists" in str(e.data).lower():
                    raise ValidationError(f"Branch already exists in GitHub: {branch_name}")
                else:
                    raise ValidationError(f"GitHub error: {e.data.get('message', str(e))}")
        except GithubException as e:
            raise ValidationError(f"GitHub connection error: {e.data.get("message", str(e))}")
        except Exception as e:
            raise ValidationError(f"Error creating GitHub branch: {str(e)}")

        if not serializer.validated_data.get('url'):
            serializer.validated_data['url'] = f"https://github.com/{settings.GITHUB_REPO_NAME}/tree/{branch_name}"
        serializer.save(task_id=task_id)
    
    def perform_update(self, serializer):
        from github import Github, GithubException
        from django.conf import settings

        old_instance = self.get_object()
        old_name = old_instance.name
        new_name = serializer.validated_data.get('name', old_name)

        if old_name != new_name:
            try:
                with transaction.atomic():
                    g = Github(settings.GITHUB_ACCESS_TOKEN)
                    repo = g.get_repo(settings.GITHUB_REPO_NAME)
                    try:
                        repo.get_branch(new_name)
                        raise ValidationError(f"New branch already exists in GitHub: {new_name}")
                        github_operation_successful = False
                    except GithubException as e:
                        if e.status != 404:
                            raise ValidationError(f"GitHub error checkng new branch: {e.data.get("message", str(e))}")
                    old_branch = repo.get_branch(old_name)
                    source_sha = old_branch.commit.sha
                    repo.create_git_ref(f"refs/heads/{new_name}", sha=source_sha)
                    print(f"Created new GitHub branch: {new_name} from old branch {old_name}")
                    if not serializer.validated_data.get("url"):
                        serializer.validated_data["url"] = f"https://github.com/{settings.GITHUB_REPO_NAME}/tree/{new_name}"
                    serializer.save()

                    repo.get_git_ref(f"heads/{old_name}").delete()
                    print(f"Delete old GitHub branch: {old_name}")
            except GithubException as e:
                raise ValidationError(f"GitHub error during rename: {e.data.get("message", str(e))}")
            except Exception as e:
                raise ValidationError(f"Error renaming GitHub branch: {str(e)}")
        else:
            serializer.save()
    
    def perform_destroy(self, instance):
        from github import Github, GithubException
        from django.conf import settings
        branch_name = instance.name
        try:
            g = Github(settings.GITHUB_ACCESS_TOKEN)
            repo = g.get_repo(settings.GITHUB_REPO_NAME)
            try:
                repo.get_git_ref(f"heads/{branch_name}").delete()
                print(f"Deleted GitHub branch: {branch_name}")
            except GithubException as e:
                if e.status == 404:
                    raise ValidationError(f"Branch not found in GitHub: {branch_name}")
                else:
                    raise ValidationError(f"GitGub deletion error: {e.data.get("message", str(e))}")

        except GithubException as e:
            raise ValidationError(f"GitHub connection error: {e.data.get("message", str(e))}")
        except Exception as e:
            raise ValidationError(f"Error deleting GitHub branch: {str(e)}")
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

