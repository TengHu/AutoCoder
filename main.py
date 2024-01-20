import os

from autocoder.bot import AutoCoder
from autocoder.index import RepositoryIndex

assert os.environ["LANGCHAIN_API_KEY"]
assert os.environ["GITHUB_APP_ID"]
assert os.environ["GITHUB_APP_PRIVATE_KEY"]

# If use OpenAI API
assert os.environ["OPENAI_API_KEY"]


os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_TRACING_V2"] = "true"

project_name = "autocoder"
os.environ["LANGCHAIN_PROJECT"] = project_name  # Optional: "default" is used if not set


# github_repository = "TengHu/auto_coder"
# github_api = GitHubAPIWrapper(
#     github_repository=github_repository,
#     github_app_id=os.environ["GITHUB_APP_ID"],
#     github_app_private_key=os.environ["GITHUB_APP_PRIVATE_KEY"],
# )

# index = RepositoryIndex(github_api, github_repository)

while True:
    try:
        user_input = input('Enter your query or type "exit" to leave: ')
        if user_input.lower() == "exit":
            break
        res = "hello"
        # TODO: stream res to the user
        print(res)
    except KeyboardInterrupt:
        break
