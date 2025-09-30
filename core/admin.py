from django.contrib import admin
from .models import Task, UserTask, User, Status, BranchesTask

admin.site.register(Task)
admin.site.register(UserTask)
admin.site.register(User)
admin.site.register(Status)
admin.site.register(BranchesTask)   