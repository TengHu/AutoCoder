import os

from actionweaver.llms import patch
from langsmith.run_helpers import traceable as _traceable

os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_TRACING_V2"] = "true"
project_name = "autocoder"
os.environ["LANGCHAIN_PROJECT"] = project_name  # Optional: "default" is used if not set

assert os.environ["LANGCHAIN_API_KEY"]


def identity_decorator(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return result

    return wrapper


def traceable(*args, **kwargs):
    if os.environ.get("LANGCHAIN_API_KEY"):
        return _traceable(*args, **kwargs)
    return identity_decorator


def trace_client(client):
    client.chat.completions.create = _traceable(name="llm_call", run_type="llm")(
        client.chat.completions.create
    )
    client = patch(client)
    client.chat.completions.create = _traceable(
        name="chat_completion_create", run_type="llm"
    )(client.chat.completions.create)
    return client
