from .models import BranchesTask

def create_branch_task_for_participant(user_task):
    task = user_task.task
    slug = task.slug or "no-slug"
    branch_name = f"{task.type}/{task.id}/{slug}-{user_task.role}"

    branch = BranchesTask.objects.create(
        name=branch_name,
        url="http://gitlab.example.com/placeholder",
        task=task
    )
    return branch