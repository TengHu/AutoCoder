import os

from actionweaver.llms import patch
from bot import AutoCoder
from langchain_community.utilities.github import GitHubAPIWrapper
from langsmith.run_helpers import traceable

from autocoder.rag import RepositoryIndex

assert os.environ["LANGCHAIN_API_KEY"]
assert os.environ["GITHUB_APP_ID"]
assert os.environ["GITHUB_APP_PRIVATE_KEY"]

# If use OpenAI API
assert os.environ["OPENAI_API_KEY"]


os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_TRACING_V2"] = "true"

project_name = "autocoder"
os.environ["LANGCHAIN_PROJECT"] = project_name  # Optional: "default" is used if not set


github_repository = "TengHu/auto_coder"
github_api = GitHubAPIWrapper(
    github_repository=github_repository,
    github_app_id=os.environ["GITHUB_APP_ID"],
    github_app_private_key=os.environ["GITHUB_APP_PRIVATE_KEY"],
)

index = RepositoryIndex(github_api, github_repository)

auto_coder = AutoCoder(github_api, None)
res = auto_coder("What are the open issues?")
print(res)
