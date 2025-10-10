from rest_framework import serializers
from .models import Task, User, UserTask, BranchesTask
from .utils import create_branch_task_for_participant

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'first_name', 'last_name')
        extra_kwargs = {
            "password": {'write_only': True}
        }
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user

class BranchesTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = BranchesTask
        fields = ("id", "name", "url", "task")
        read_only_fields = ("task",)

class TaskSerializer(serializers.ModelSerializer):
    status_name = serializers.CharField(source='status.name', read_only=True)

    class Meta:
        model = Task

        fields = ("id", "name", "description", "status", "status_name", "type", "planned_time", "slug")
        extra_kwargs = {'status': {'write_only': True}}

    def create(self, validated_data):
        user = self.context['request'].user
        task = Task.objects.create(**validated_data)
        user_task = UserTask.objects.create(
            user=user,
            task=task,
            role=UserTask.Role.OWNER
        )
        create_branch_task_for_participant(user_task)
        return task

class UserTaskSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = UserTask
        fields = ("id", "user", "user_name", "task", "work_time", "role")
        read_only_fields = ('task', 'work_time')

    def create(self, validated_data):
        task_id = self.context['view'].kwargs['task_pk']
        validated_data['task_id'] = task_id
        user_task = super().create(validated_data)
        create_branch_task_for_participant(user_task)
        return user_task

class ManageParticipantSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    role = serializers.ChoiceField(choices=UserTask.Role.choices)

class LogWorkTimeSerializer(serializers.ModelSerializer):
    hours = serializers.DecimalField(max_digits=5, decimal_places=2, write_only=True)

    class Meta:
        model = UserTask
        fields = ("id", "user", "task", "work_time", "role")
        read_only_fields = ('id', 'user', 'task', 'role')

    def update(self, instance, validated_data):
        hours_to_add = validated_data.get('hours', 0)
        current_work_time = instance.work_time or 0
        instance.work_time = current_work_time + hours_to_add
        instance.save()
        return instance
        
