from .models import BranchesTask
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
    