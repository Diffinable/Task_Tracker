from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Task, UserTask, User, Status, BranchesTask

class CustomUserAdmin(UserAdmin):
    list_display = ('id',) + UserAdmin.list_display
    list_display_links = ('id', 'username')

admin.site.register(Task)
admin.site.register(UserTask)
admin.site.register(Status)
admin.site.register(BranchesTask)   

admin.site.register(User, CustomUserAdmin)
