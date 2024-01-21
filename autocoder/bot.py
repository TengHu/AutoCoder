import os
from typing import List

from actionweaver import action
from actionweaver.utils.tokens import TokenUsageTracker
from openai import OpenAI

from autocoder.pydantic_models.context import create_context, gather_context
from autocoder.pydantic_models.file_ops import create_implementation_plan
from autocoder.telemetry import trace_client, traceable

assert os.environ["MODEL"]
MODEL = os.environ["MODEL"]


class AutoCoder:
    def __init__(self, github_api, index, codebase):
        self.github_api = github_api

        # self.client = trace_client(AzureOpenAI(
        #     azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"),
        #     api_key=os.getenv("AZURE_OPENAI_KEY"),
        #     api_version="2023-10-01-preview"
        # ))
        self.client = trace_client(OpenAI())
        self.messages = [
            {
                "role": "system",
                "content": "You are a coding assistant, you have the capability to assist with code-related tasks and modify files.",
            },
        ]
        self.index = index
        self.codebase = codebase

        msg = self.create_branch(f"aw_demo_bot")
        print(f"[System] {msg}")

    def __call__(self, input: str):
        self.messages.append({"role": "user", "content": input})

        response = self.client.chat.completions.create(
            model=MODEL,
            messages=self.messages,
            stream=False,
            temperature=0.1,
            actions=[
                self.get_issues,
                self.question_answer,
                self.create_pull_request,
                self.plan_code_change,
            ],
            orch={
                self.plan_code_change.name: self.summarize_changes,
                self.create_pull_request.name: None,
            },
            token_usage_tracker=TokenUsageTracker(500),
        )

        content = ""
        try:
            content = response.choices[0].message.content
        except:
            content = str(response)
        self.messages.append({"role": "assistant", "content": content})
        return content

    @action(name="QuestionAnswer", decorators=[traceable(run_type="tool")])
    def question_answer(self, rewritten_query: str, keywords: List[str]):
        """Answer questions about the codebase"""

        context = gather_context(
            " ".join(keywords), self.client, self.index, self.codebase
        )

        messages = [
            {
                "role": "user",
                "content": f"{context} \n###########\n Question: {rewritten_query}",
            }
        ]
        response = self.client.chat.completions.create(
            model=MODEL,
            messages=messages,
            stream=False,
            token_usage_tracker=TokenUsageTracker(500),
        )
        return response

    @action(name="GetIssues", decorators=[traceable(run_type="tool")])
    def get_issues(self):
        """
        Get a list of issues from the GitHub repo.
        """
        response = self.github_api.get_issues()
        response = response.split("\n")
        return eval(response[1]) if len(response) > 1 else []

    @action(name="CreateGitBranch", decorators=[traceable(run_type="tool")])
    def create_branch(self, branch: str):
        """
        Create a new Git branch.
        """
        return self.github_api.create_branch(branch)

    @action(name="CreatePullRequest", decorators=[traceable(run_type="tool")])
    def create_pull_request(self, title: str, description: str):
        """
        Create a new Pull Request in a Git repository.

        Args:
            title (str): The title of the Pull Request.
            description (str): The description of the Pull Request.
        """
        return (
            f"Current branch {self.github_api.active_branch}\n"
            + self.github_api.create_pull_request(pr_query=f"{title}\n {description}")
        )

    @action(
        "PlanAndImplementCodeChange",
        stop=False,
        decorators=[traceable(run_type="tool")],
    )
    def plan_code_change(self, instruction: str):
        """
        Plan and implement code changes based on a given description.

        This method is designed to handle various types of code alterations such as
        inserting new code, refactoring existing code, replacing segments, or making
        general modifications.
        """
        context = gather_context(instruction, self.client, self.index, self.codebase)

        messages = [
            {
                "role": "user",
                "content": (
                    f"{context}\n"
                    + "<user_instruction>\n"
                    + f"{instruction}\n"
                    + "</user_instruction>\n"
                ),
            }
        ]
        implementation_plan = create_implementation_plan.invoke(
            self.client,
            messages=messages,
            temperature=1,
            model=MODEL,
            stream=False,
            force=True,
        )

        if isinstance(implementation_plan, list):
            implementation_plan = implementation_plan[0]
        messages = implementation_plan.execute(
            self.client, self.github_api, self.index, self.codebase
        )

        files_updated = []
        files_created = []
        problems = []
        for msg in messages:
            if "Updated file" in str(msg):
                files_updated.append(msg)
            elif "Created file" in str(msg):
                files_created.append(msg)
            else:
                problems.append(msg)

        return f"""
I've modified and updated the codebase according to your request in {self.github_api.active_branch} branch. Here's what I've done:
- New files created: {files_created}
- Existing files updated: {files_updated}
- Problems encountered: {problems}

Is there anything else I can help you with?
"""

    def search_code(self, query: str):
        return self.github_api.search_code(query)

    @action(name="SummarizeChanges", stop=True, decorators=[traceable(run_type="tool")])
    def summarize_changes(self, msg: str):
        """Summarize the changes made in the previous step."""
        messages = [
            {"role": "user", "content": f"{msg}\n####\n Summarize the message above"}
        ]
        response = self.client.chat.completions.create(
            model=MODEL,
            messages=messages,
            stream=False,
            temperature=0.1,
            token_usage_tracker=TokenUsageTracker(500),
        )
        content = ""
        try:
            content = response.choices[0].message.content
        except:
            content = str(response)
        return content

    def refresh(self):
        self.codebase.clear_cache()
        self.index.setup()
