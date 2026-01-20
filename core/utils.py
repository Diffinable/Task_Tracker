from github import Github, GithubException
from .services import GitHubService
from django.conf import settings
from rest_framework.exceptions import ValidationError


def create_branch_and_task_record(user_task):
    from .models import BranchesTask
    task = user_task.task
    branch_name = create_branch_name(task, user_task)

    try:
        gh_service = GitHubService()
        
        branch_url = gh_service.create_branch(branch_name)
        branch_task, created = BranchesTask.objects.update_or_create(
            user_task=user_task,
            defaults={
                "url": branch_url,
                "task": task,
                "name": branch_name
            }
        )
        print(f"BranchTask record {'created' if created else 'updated'} for branch: {branch_name}")
        return branch_task
    except ValidationError as e:
        print(f"Validation error creating branch: {branch_name}")
        return None
    except Exception as e:
        print(f"Error creating branch {branch_name} - {str(e)}")
        return None
    

def update_branches_for_task(task, old_slug, old_type):
    """
    Recreates branches for all participants if task details (slug, type) changed.
    old_task_data: A dictionary containing the old values of the task fields.
    """
    from .models import UserTask, BranchesTask
    if task.slug == old_slug and task.type == old_type:
        return 

    try:
        gh_service = GitHubService()
    except Exception as e:
        print(f"GitHub service init failed: {e}")
        return

    user_tasks = UserTask.objects.filter(task=task).select_related('user')

    for user_task in user_tasks:
        old_branch_name = create_branch_name(
            task, user_task, custom_slug=old_slug, custom_type=old_type
        )
        new_branch_name = create_branch_name(task, user_task)
        if old_branch_name == new_branch_name:
            continue
        try:
            new_branch_url = gh_service.rename_branch(old_branch_name, new_branch_name)
            BranchesTask.objects.update_or_create(
                user_task=user_task,
                defaults={
                    "name": new_branch_name,
                    "url": new_branch_url,
                    "task": task
                }
            )
            print(f"Branch in database updated: {old_branch_name} -> {new_branch_name}")          
        except ValidationError as e:
            print(f"GitHub rename failed: {e}")    
        except Exception as e:
            print(f"Unexpected error: {e}")


def create_branch_name(task, user_task, custom_slug=None, custom_type=None):
    """
    Generates a consistent  branch name
    """
    slug = custom_slug if custom_slug else (task.slug or "no-slug")
    task_type = custom_type if custom_type else task.type
    username = user_task.user.username if user_task.user else 'unknown'
    return f"{task_type}/{task.id}/{slug}-{username}-{user_task.role}"
