from github import Github, GithubException
from django.conf import settings

def create_branch_and_task_record(user_task):
    from .models import BranchesTask
    task = user_task.task
    slug = task.slug or "no-slug"
    username = user_task.user.username if user_task.user else 'unknown'
    branch_name = f"{task.type}/{task.id}/{slug}-{username}-{user_task.role}"

    try:
        g = Github(settings.GITHUB_ACCESS_TOKEN)
        repo = g.get_repo(settings.GITHUB_REPO_NAME)

        try:
            source_branch = repo.get_branch('main')
            source_sha = source_branch.commit.sha
            repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=source_sha)
            print(f"Created Github branch {branch_name}")

        except GithubException as e:
            if e.status == 422 and "already exists" in str(e.data).lower():
                print(f"Branch already exists in Github: {branch_name}")
            else:
                raise
        branch_url = f"https://github.com/{settings.GITHUB_REPO_NAME}/tree/{branch_name}"
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
    except GithubException as e:
        print(f"GitHub error {e.status}, {e.data}")
        return None
    except Exception as e:
        print(f"Error: Could not create branch or DB record for {branch_name}. Reason: {repr(e)}")
        return None

def recreate_branches_for_slug_change(task, old_slug):
    from .models import UserTask, BranchesTask
    user_tasks = UserTask.objects.filter(task=task).select_related('user')
    g = Github(settings.GITHUB_ACCESS_TOKEN)
    repo = g.get_repo(settings.GITHUB_REPO_NAME)
    branches_updated = 0
    errors = []
    for user_task in user_tasks:
        username = user_task.user.username if user_task.user else 'unknown'
        old_branch_name = f"{task.type}/{task.id}/{old_slug}-{username}-{user_task.role}"
        new_branch_name = f"{task.type}/{task.id}/{task.slug}-{username}-{user_task.role}"
        try:
            if old_branch_name == new_branch_name:
                print(f"Branch name unchanged for user {user_task.user.username}")
                continue

            try:
                old_ref = repo.get_git_ref(f"heads/{old_branch_name}")
                source_sha = old_ref.object.sha
                print(f"Found old branch {old_branch_name}")
            except GithubException:
                source_branch = repo.get_branch('main')
                source_sha = source_branch.commit.sha
                print(f"Old branch not found, using main branch: {old_branch_name}")
            try:
                repo.create_git_ref(ref=f'refs/heads/{new_branch_name}', sha=source_sha)
                print(f"Created new branch: {new_branch_name}")
            except GithubException as e:
                if e.status == 422 and "already exists" in str(e):
                    pass
                else:
                    raise


            try:
                repo.get_git_ref(f"heads/{old_branch_name}").delete()
                print(f"Delete old branch: {old_branch_name}")
            except GithubException:
                print(f"Could not delete old branch (may not exist): {old_branch_name}")
                pass

            branch_task, created = BranchesTask.objects.update_or_create(
                user_task=user_task,
                defaults={
                    "name": new_branch_name,
                    "url": f"https://github.com/{settings.GITHUB_REPO_NAME}/tree/{new_branch_name}",
                    "task": task
                }
            )
            print(f"Recreated branch due to slug change: {old_branch_name} -> {new_branch_name}")
            branches_updated += 1
            
        except GithubException as e:
            print(f"Error {user_task.user.username}: {e.status} - {e.data}")
        except Exception as e:
            print(f"Error {user_task.user.username}: {repr(e)}")
    return {'branches_updated': branches_updated, "errors": errors}
    
def recreate_branches_for_all_participants(task, old_task):
    from .models import UserTask, BranchesTask
    user_tasks = UserTask.objects.filter(task=task).select_related('user')
    g = Github(settings.GITHUB_ACCESS_TOKEN)
    repo = g.get_repo(settings.GITHUB_REPO_NAME)
    branches_updated = 0
    errors = []
    for user_task in user_tasks:
        username = user_task.user.username if user_task.user else 'unknown'
        if hasattr(old_task, 'slug') and old_task.slug:
            old_branch_name = f"{old_task.type}/{old_task.id}/{old_task.slug}-{username}-{user_task.role}"
        else:
            old_branch_name = create_branch_name(old_task, user_task)

        new_branch_name = create_branch_name(task, user_task)
        try:
            if old_branch_name == new_branch_name:
                print(f"Branch name unchanged for user: {user_task.user.username}")
                continue

            try:
                old_ref = repo.get_git_ref(f"heads/{old_branch_name}")
                source_sha = old_ref.object.sha
                print(f"Found old branch {old_branch_name}")
            except GithubException:
                source_branch = repo.get_branch('main')
                source_sha = source_branch.commit.sha
                print(f"Old branch not found, using main branch: {old_branch_name}")

            try:
                repo.create_git_ref(ref=f'refs/heads/{new_branch_name}', sha=source_sha)
                print(f"Created new branch: {new_branch_name}")
            except GithubException as e:
                if e.status == 422 and "already exists" in str(e.data).lower():
                    print(f"New branch already exists: {new_branch_name}")
                else:
                    raise

            if old_branch_name != new_branch_name:

                try:
                    repo.get_git_ref(f"heads/{old_branch_name}").delete()
                    print(f"Delete old branch: {old_branch_name}")
                except GithubException:
                    print(f'Deleted old branch: {old_branch_name}')
                    pass

            branch_task, created = BranchesTask.objects.update_or_create(
                user_task=user_task,
                defaults= {
                    'name': new_branch_name,
                    'url': f"https://github.com/{settings.GITHUB_REPO_NAME}/tree/{new_branch_name}",
                    "task": task
                }
            )
            print(f"Recreated branch due to slug change: {old_branch_name} -> {new_branch_name}")
            branches_updated += 1
            
        except GithubException as e:
            print(f"Error {user_task.user.username}: {e.status} - {e.data}")
        except Exception as e:
            print(f"Error {user_task.user.username}: {repr(e)}")
    return {'branches_updated': branches_updated, "errors": errors}

def delete_old_branches(task):
    from .models import BranchesTask
    g = Github(settings.GITHUB_ACCESS_TOKEN)
    repo = g.get_repo(settings.GITHUB_REPO_NAME)

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
    username = user_task.user.username if user_task.user else 'unknown'
    return f"{task.type}/{task.id}/{slug}-{username}-{user_task.role}"
