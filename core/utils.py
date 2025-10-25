from .models import BranchesTask, UserTask
from github import Github, GithubException
from django.conf import settings

def create_branch_and_task_record(user_task):
    task = user_task.task
    slug = task.slug or "no-slug"
    branch_name = f"{task.type}/{task.id}/{slug}-{user_task.role}"

    try:
        g = Github(settings.GITHUB_ACCESS_TOKEN)
        repo = g.get_repo(settings.GITHUB_REPO_NAME)
        source_branch = repo.get_branch('main')
        source_sha = source_branch.commit.sha
        repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=source_sha)
        branch_url = f"https://github.com/{settings.GITHUB_REPO_NAME}/tree/{branch_name}"
        BranchesTask.objects.create(
            name=branch_name,
            url=branch_url,
            task=task
        )
        print(f"BranchTask record created for branch: {branch_name}")

    except GithubException as e:
        print(f"Github error: {e.status} - {e.data}")
    except Exception as e:
        print(f"Error: Could not create branch or DB record for {branch_name}. Reason: {repr(e)}")

def recreate_branches_for_all_participants(task, old_task):
    user_tasks = UserTask.objects.filter(task=task).select_related('user')
    g = Github(settings.GITHUB_ACCESS_TOKEN)
    repo = g.get_repo(settings.GITHUB_REPO_NAME)
    for user_task in user_tasks:
        old_branch_name = create_branch_name(old_task, user_task)
        new_branch_name = create_branch_name(task, user_task)
        try:
            old_ref = repo.get_git_ref(f"heads/{old_branch_name}")
            source_sha = old_ref.object.sha
        except GithubException:
            source_sha = repo.get_branch('main').commit.sha
        repo.create_git_ref(ref='refs/heads/{new_branch_name}', sha=source_sha)
        if old_branch_name != new_branch_name:
            try:
                repo.get_git_ref(f"heads/{old_branch_name}").delete()
                print(f"Delete old branch: {old_branch_name}")
            except GithubException:
                pass

        BranchesTask.objects.filter(task=task, name=old_branch_name).delete()

        BranchesTask.objects.create(
            task=task,
            name=new_branch_name,
            url=f"https://github.com/{settings.GITHUB_REPO_NAME}/tree/{new_branch_name}"
        )
        print(f'Recreated branch: {old_branch_name} -> {new_branch_name}')
        
        create_branch_and_task_record(user_task)

def create_branch_name(task, user_task):
    slug = task.slug or "no-slug"
    return f"{task.type}/{task.id}/{slug}-{user_task.role}"
