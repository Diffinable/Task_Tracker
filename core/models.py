from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    pass

class UserTask(models.Model):
    class Role(models.TextChoices):
        OWNER = 'owner'
        EXECUTOR = 'executor'

    user = models.ForeignKey("User", on_delete=models.PROTECT)
    task = models.ForeignKey("Task", on_delete=models.PROTECT)
    work_time = models.DecimalField(max_digits=10, decimal_places=2)
    role = models.CharField(choices=Role.choices)

class Task(models.Model):
    class TaskType(models.TextChoices):
        FEATURE = "feature"
        BUGFIX = "bugfix"
        HOTFIX = "hotfix"

    name = models.CharField()
    description = models.CharField(blank=True, null=True)
    status = models.ForeignKey("Status", on_delete=models.PROTECT)
    type = models.CharField(choices=TaskType.choices)
    planned_time = models.DecimalField(max_digits=10, decimal_places=2)
    slug = models.CharField()

class Status(models.Model):
    name = models.CharField()

class BranchesTask(models.Model):
    name = models.CharField()
    url = models.CharField(blank=True, null=True)
    task = models.ForeignKey("Task", on_delete=models.PROTECT)

