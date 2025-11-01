from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
from core.utils import recreate_branches_for_slug_change


class User(AbstractUser):
    pass

class UserTask(models.Model):
    class Role(models.TextChoices):
        OWNER = 'owner'
        EXECUTOR = 'executor'

    user = models.ForeignKey("User", on_delete=models.PROTECT, blank=True, null=True)
    task = models.ForeignKey("Task", on_delete=models.CASCADE, blank=True, null=True)
    work_time = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    role = models.CharField(choices=Role.choices, blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['task', 'user'],
                name='unique_user_task_participant'
            )
        ]

class Task(models.Model):
    class TaskType(models.TextChoices):
        FEATURE = "feature"
        BUGFIX = "bugfix"
        HOTFIX = "hotfix"

    name = models.CharField()
    description = models.CharField(blank=True, null=True)
    status = models.ForeignKey("Status", on_delete=models.PROTECT, blank=True, null=True)
    type = models.CharField(choices=TaskType.choices, default=2, blank=True, null=True)
    planned_time = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    slug = models.CharField(unique=True ,blank=True, null=True)

    def save(self, *args, **kwargs):
        old_slug = None
        if self.pk:
            old_task = Task.objects.filter(pk=self.pk).first()
            if old_task:
                old_slug = old_task.slug

        if not self.slug or (self.pk and old_slug and old_slug != f"{slugify(self.name)}-{self.pk}"):
            self.slug = f"{slugify(self.name)}-{self.pk}"
        super().save(*args, **kwargs)

        if old_slug and old_slug != self.slug:
            recreate_branches_for_slug_change(self, old_slug)

class Status(models.Model):
    name = models.CharField(max_length=50, unique=True)

class BranchesTask(models.Model):
    name = models.CharField()
    url = models.CharField(blank=True, null=True)
    task = models.ForeignKey("Task", on_delete=models.SET_NULL, blank=True, null=True)
    user_task = models.ForeignKey(UserTask, on_delete=models.CASCADE, blank=True, null=True)

