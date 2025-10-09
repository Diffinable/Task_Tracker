from rest_framework import serializers
from .models import Task, User, UserTask

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

class TaskSerializer(serializers.ModelSerializer):
    status_name = serializers.CharField(source='status.name', read_only=True)

    class Meta:
        model = Task

        fields = ("id", "name", "description", "status", "status_name", "type", "planned_time", "slug")
        extra_kwargs = {'status': {'write_only': True}}

class UserTaskSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = UserTask

        fields = ("id", "user", "user_name", "task", "work_time", "role")
        read_only_fields = ('task', 'work_time')

class ManageParticipantSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    role = serializers.ChoiceField(choices=UserTask.Role.choices)

class LogWorkTimeSerializer(serializers.Serializer):
    hours = serializers.DecimalField(max_digits=5, decimal_places=2)
