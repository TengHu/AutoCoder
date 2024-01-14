import os
from langchain_community.utilities.github import GitHubAPIWrapper

def check_file_exists(repo, file_path):
    github_api = GitHubAPIWrapper(
        github_repository=repo,
        github_app_id=os.environ['GITHUB_APP_ID'],
        github_app_private_key=os.environ['GITHUB_APP_PRIVATE_KEY'],
    )
    try:
        github_api.get_file(file_path)
        return True
    except FileNotFoundError:
        return False
