from django.db import models

class User(models.Model):
    first_name = models.CharField()
    last_name = models.CharField()
    username = models.CharField()
    password = models.CharField()

class UserTask(models.Model):
    user = models.ForeignKey("User")
    task = models.ForeignKey("Task")

class Task(models.Model):
    name = models.CharField()
    description = models.CharField(blank=True, null=True)
    status = models.ForeignKey("Status")
    type = models.Choices(["feature", "bugfix", "hotfix"])
    planned_time = models.DecimalField()
    slug = models.CharField()

class Status(models.Model):
    name = models.CharField()

class BranchesTask(models.Model):
    name = models.CharField()
    url = models.CharField(blank=True, null=True)
    task = models.ForeignKey("Task")

