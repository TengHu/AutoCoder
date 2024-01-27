import os

from actionweaver.llms import patch
from langsmith.run_helpers import traceable as _traceable

os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_TRACING_V2"] = "true"
project_name = "autocoder"
os.environ["LANGCHAIN_PROJECT"] = project_name  # Optional: "default" is used if not set

assert os.environ["LANGCHAIN_API_KEY"]





def traceable(*args, **kwargs):
    return _traceable(*args, **kwargs)


def trace_client(client):
    # TODO: replace traceable to _traceable, no need to use traceable because LANGCHAIN_API_KEY is already checked
    if os.environ.get("LANGCHAIN_API_KEY"):
        client.chat.completions.create = traceable(name="llm_call", run_type="llm")(
            client.chat.completions.create
        )
        client = patch(client)
        client.chat.completions.create = traceable(
            name="chat_completion_create", run_type="llm"
        )(client.chat.completions.create)
        return client
    else:
        return patch(client)
