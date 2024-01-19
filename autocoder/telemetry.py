import os

from actionweaver.llms import patch
from langsmith.run_helpers import traceable

os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_TRACING_V2"] = "true"
project_name = "autocoder"
os.environ["LANGCHAIN_PROJECT"] = project_name  # Optional: "default" is used if not set

assert os.environ["LANGCHAIN_API_KEY"]



