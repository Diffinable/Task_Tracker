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
        branch_task, created = BranchesTask.objects.get_or_create(
            task=task,
            name=branch_name,
            url=branch_url
        )
        if not created:
            branch_task.name = branch_name
            branch_task.url = branch_url
            branch_task.save()
        print(f"BranchTask record {'created' if created else 'updated'} for branch: {branch_name}")
        return branch_task

    except GithubException as e:
        print(f"Github error: {e.status} - {e.data}")
        return None
    except Exception as e:
        print(f"Error: Could not create branch or DB record for {branch_name}. Reason: {repr(e)}")
        return None

def recreate_branches_for_all_participants(task, old_task):
    user_tasks = UserTask.objects.filter(task=task).select_related('user')
    g = Github(settings.GITHUB_ACCESS_TOKEN)
    repo = g.get_repo(settings.GITHUB_REPO_NAME)
    branches_updated = 0
    errors = []
    for user_task in user_tasks:
        old_branch_name = create_branch_name(old_task, user_task)
        new_branch_name = create_branch_name(task, user_task)
        try:
            if old_branch_name == new_branch_name:
                continue

            try:
                old_ref = repo.get_git_ref(f"heads/{old_branch_name}")
                source_sha = old_ref.object.sha
            except GithubException:
                source_sha = repo.get_branch('main').commit.sha

            repo.create_git_ref(ref='refs/heads/{new_branch_name}', sha=source_sha)

            try:
                repo.get_git_ref(f"heads/{old_branch_name}").delete()
                print(f"Delete old branch: {old_branch_name}")
            except GithubException:
                pass

            branch_task, created = BranchesTask.objects.update_or_create(
                task=task,
                name=old_branch_name,
                defaults= {
                    'name': new_branch_name,
                    'url': f"https://github.com/{settings.GITHUB_REPO_NAME}/tree/{new_branch_name}"
                }
            )
            branches_updated += 1
            BranchesTask.objects.filter(task=task, name=old_branch_name).delete()

            print(f'Recreated branch: {old_branch_name} -> {new_branch_name}')
            
            create_branch_and_task_record(user_task)
        except GithubException as e:
            print(f"Error {user_task.user.username}: {e.status} - {e.data}")
        except Exception as e:
            print(f"Error {user_task.user.username}: {repr(e)}")
        return {'branches_updated': branches_updated}

def delete_old_branches(task):
    g = Github(settings.GITHUB_ACCESS_TOKEN)
    repo = Github(settings.GITHUB_REPO_NAME)

    task_branches = BranchesTask.objects.filter(task=task).values_list('name', flat=True)
    current_branch_names = set(task_branches)

    all_branches = repo.get_branches()
    deleted_count = 0

    for branch in all_branches:
        branch_name = branch.name
        if branch_name.startswith(f"{task.type}/{task.id}/") and branch_name not in current_branch_names:
            try:
                repo.get_git_ref(f"heads/{branch_name}").delete()
                print(f"Deleted branch = {branch_name}")
                deleted_count += 1
            except GithubException as e:
                print(f"Failed to delete branch: {branch_name} - {e}")
    
    return deleted_count


def create_branch_name(task, user_task):
    slug = task.slug or "no-slug"
    return f"{task.type}/{task.id}/{slug}-{user_task.role}"
