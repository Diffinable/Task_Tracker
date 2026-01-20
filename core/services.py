from github import Github, GithubException
from django.conf import settings
from rest_framework.exceptions import ValidationError

class GitHubService:
    def __init__(self):
        if not settings.GITHUB_ACCESS_TOKEN or not settings.GITHUB_REPO_NAME:
            raise ValidationError(f"GitHub configuration is missing in settings")

        self.client = Github(settings.GITHUB_ACCESS_TOKEN)
        try:
            self.repo = self.client.get_repo(settings.GITHUB_REPO_NAME)
        except Exception as e:
            raise ValidationError(f"Could not connect to GitHub repo: {str(e)}")

    def create_branch(self, branch_name, source_branch="main"):
        """Created a branch in GitHub"""
        try:
            source_branch = self.repo.get_branch(source_branch)
            source_sha = source_branch.commit.sha
            self.repo.create_git_ref(f"refs/heads/{branch_name}", sha=source_sha)
            return f"https://github.com/{settings.GITHUB_REPO_NAME}/tree/{branch_name}"
        except GithubException as e:
            if e.status == 422 and "already exists" in str(e.data).lower():
                raise ValidationError(f"Branch already exists in GitHub: {branch_name}")
            else:
                raise ValidationError(f"GitHub error: {e.data.get('message', str(e))}")

    def rename_branch(self, old_name, new_name):
        """Renames branch by creating a new one and deleting the old one"""
        try:
            self.repo.get_branch(new_name)
            raise ValidationError(f"New branch already exists in GitHub: {new_name}")
        except GithubException as e:
            if e.status != 404:
                raise ValidationError(f"GitHub error checkng new branch: {e.data.get("message", str(e))}")
        try:
            old_branch = self.repo.get_branch(old_name)
            source_sha = old_branch.commit.sha
            self.repo.create_git_ref(f"refs/heads/{new_name}", sha=source_sha)
        except Exception as e:
            raise ValidationError(
                f"Failed to create a new branch '{new_name}' (Old branch {old_name} missing): {str(e)}"
            )
        self.delete_branch(old_name)

        return f"https://github.com/{settings.GITHUB_REPO_NAME}/tree/{new_name}"

    def delete_branch(self, branch_name):
        try:
            ref = self.repo.get_git_ref(f"heads/{branch_name}")
            ref.delete()
            print(f"Deleted GitHub branch: {branch_name}")
        except GithubException as e:
            if e.status == 404:
                pass
            else:
                raise ValidationError(f"GitGub deletion error: {e.data.get("message", str(e))}")
