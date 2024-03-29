import os

from langchain_community.utilities.github import GitHubAPIWrapper
from llama_index.llms import AzureOpenAI as LlamaIndexAzureOpenAI
from openai import AzureOpenAI

from autocoder.bot import AutoCoder
from autocoder.codebase import Codebase
from autocoder.index import RepositoryIndex
from autocoder.telemetry import trace_client

assert os.environ["LANGCHAIN_API_KEY"]
assert os.environ["GITHUB_APP_ID"]
assert os.environ["GITHUB_APP_PRIVATE_KEY"]


# If use OpenAI API
assert os.environ["OPENAI_API_KEY"]


os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_TRACING_V2"] = "true"

project_name = "autocoder"
os.environ["LANGCHAIN_PROJECT"] = project_name  # Optional: "default" is used if not set


def bold_green_string(text):
    bold_green_text = "\033[1;32m" + text + "\033[0m"
    return bold_green_text


def bold_blue_string(text):
    bold_blue_text = "\033[1;34m" + text + "\033[0m"
    return bold_blue_text


def stream_string_to_terminal(s, delay=0.1):
    import time

    for char in s:
        print(char, end="", flush=True)
        time.sleep(delay)
    print()  # for newline after streaming


llm = trace_client(
    AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        api_version="2023-10-01-preview",
    )
)

llm_for_rag = LlamaIndexAzureOpenAI(
    engine=os.environ["MODEL"],
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2023-10-01-preview",
    use_azure_ad=False,
)
github_repository = "TengHu/auto_coder"
github_api = GitHubAPIWrapper(
    github_repository=github_repository,
    github_app_id=os.environ["GITHUB_APP_ID"],
    github_app_private_key=os.environ["GITHUB_APP_PRIVATE_KEY"],
)
codebase = Codebase(github_api)
index = RepositoryIndex(github_repository, codebase, llm_for_rag)

autocoder = AutoCoder(index, codebase, llm, create_branch=False)


print(os.environ["MODEL"])

print(
    bold_green_string("Welcome to AutoCoder! Enter your query or type 'exit' to leave")
)
while True:
    try:
        user_input = input(bold_green_string("User :"))
        if user_input.lower() == "exit":
            break
        res = autocoder(user_input)
        print(bold_blue_string("Assistant: "))
        stream_string_to_terminal(res, 0.003)
    except KeyboardInterrupt:
        break
