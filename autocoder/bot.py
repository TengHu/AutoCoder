import os
from typing import List

from actionweaver import action
from actionweaver.utils.tokens import TokenUsageTracker
from openai import OpenAI

from autocoder.pydantic_models.context import create_context
from autocoder.pydantic_models.file_ops import create_implementation_plan
from autocoder.telemetry import trace_client, traceable

assert os.environ["MODEL"]
MODEL = os.environ["MODEL"]


DIVIDING_LINE = """
###############
This section is divider and not a part of the code.
{input}
#############

"""


class AutoCoder:
    def __init__(self, github_api, index, codebase):
        # ... existing code ...

    @action(name="GetIssues", decorators=[traceable(run_type="tool")])
    def get_issues(self):
        # ... existing code ...

    @action(name="CreateGitBranch", decorators=[traceable(run_type="tool")])
    def create_branch(self, branch: str):
        # ... existing code ...

    @action(name="CreatePullRequest", decorators=[traceable(run_type="tool")])
    def create_pull_request(self, title: str, description: str):
        # ... existing code ...

    @action(
        "PlanAndImplementCodeChange",
        stop=False,
        decorators=[traceable(run_type="tool")],
    )
    def plan_code_change(self, instruction: str):
        # ... existing code ...

    @action(name="QuestionAnswer", decorators=[traceable(run_type="tool")])
    def question_answer(self, rewritten_query: str, keywords: List[str]):
        # ... existing code ...

    def __call__(self, input: str):
        # ... existing code ...

    @traceable(run_type="tool")
    def gather_context(self, input):
        # ... existing code ...

    @traceable(run_type="tool")
    def read_files(self, files: List[str]) -> List[str]:
        # ... existing code ...

    def rephrase(self, input: str):
        # ... existing code ...

    def search_code(self, query: str):
        # ... existing code ...
        return self.github_api.search_code(query)
