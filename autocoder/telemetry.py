import os

from actionweaver.llms import patch
from langsmith.run_helpers import traceable

os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_TRACING_V2"] = "true"
project_name = "actionweaver"
os.environ["LANGCHAIN_PROJECT"] = project_name  # Optional: "default" is used if not set

assert os.environ["LANGCHAIN_API_KEY"]


@traceable(run_type="tool")
def trace_client_v2(client):
    client.chat.completions.create = traceable(name="llm_call", run_type="llm")(
        client.chat.completions.create
    )
    client = patch(client)
    client.chat.completions.create = traceable(
        name="chat_completion_create", run_type="llm"
    )(client.chat.completions.create)
    return client
