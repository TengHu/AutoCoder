import os
from typing import List

from actionweaver import action
from actionweaver.utils.tokens import TokenUsageTracker

from autocoder.pydantic_models.context import create_context, gather_context
from autocoder.pydantic_models.file_ops import create_implementation_plan
from autocoder.telemetry import trace_client, traceable
from autocoder.utils import format_debug_msg

assert os.environ["MODEL"]
MODEL = os.environ["MODEL"]


class AutoCoder:
    def __init__(self, index, codebase, llm, create_branch=False):
        self.client = llm
        self.system_message = {
            "role": "system",
            "content": "You are a coding assistant, you have the capability to assist with code-related tasks and modify files.",
        }
        self.messages = [self.system_message]
        self.index = index
        self.codebase = codebase

        if create_branch:
            self.create_branch("aw_demo_bot")

    def __call__(self, input: str):
        self.original_input = input

        self.messages.append(
            {
                "role": "user",
                "content": "<user_query>\n" + input + "\n</user_query>",
            }
        )

        response = self.client.chat.completions.create(
            model=MODEL,
            messages=self.messages,
            stream=False,
            temperature=0.3,
            actions=[
                self.get_issues,
                self.question_answer,
                self.list_all_files,
                # self.read_file,
                self.create_pull_request,
                self.plan_code_change,
                self.create_branch,
                self.set_active_branch,
            ],
            orch={
                self.plan_code_change.name: self.summarize_changes,
                self.create_pull_request.name: None,
                self.create_branch.name: None,
                self.list_all_files.name: None,
                self.set_active_branch.name: None,
                # self.read_file.name: None,
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

    # @action(name="Modify", decorators=[traceable(run_type="tool")])
    # def modify(self, input: str):
    #     """
    #     Use this if you plan to modify the codebase.
    #     """
    #     self.messages.append(
    #         {
    #             "role": "user",
    #             "content": "<user_query>\n" + input + "\n</user_query>",
    #         }
    #     )

    #     return self.client.chat.completions.create(
    #         model=MODEL,
    #         messages=self.messages,
    #         stream=False,
    #         temperature=0.1,
    #         actions=[
    #             self.create_pull_request,
    #             self.plan_code_change,
    #             self.create_branch,
    #             self.set_active_branch,
    #         ],
    #         orch={
    #             self.plan_code_change.name: self.summarize_changes,
    #             self.create_pull_request.name: None,
    #             self.create_branch.name: None,
    #             self.set_active_branch.name: None,
    #         },
    #         token_usage_tracker=TokenUsageTracker(500),
    #     )

    @action(name="CreateBranch", decorators=[traceable(run_type="tool")])
    def create_branch(self, branch: str):
        """
        Create a new Git branch.
        """

        msg = self.codebase.create_branch(branch)
        print(format_debug_msg(msg))
        return msg

    @action(name="SetActiveBranch", decorators=[traceable(run_type="tool")])
    def set_active_branch(self, branch: str):
        """
        Set the active Git branch.
        """

        print(format_debug_msg(f"Setting active branch: {branch}"))
        return self.codebase.set_active_branch(branch)

    @action(name="ListAllFiles", decorators=[traceable(run_type="tool")])
    def list_all_files(self):
        """List all files in the bot branch."""
        return self.codebase.list_files_in_bot_branch()

    @action(name="QuestionAnswer", decorators=[traceable(run_type="tool")])
    def question_answer(self, rewritten_query: str, keywords: List[str]):
        """Answer questions about the codebase"""

        print(format_debug_msg(f"Answering question: {rewritten_query}"))

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
        response = self.codebase.get_issues()
        response = response.split("\n")
        return eval(response[1]) if len(response) > 1 else []

    @action(name="CreatePullRequest", decorators=[traceable(run_type="tool")])
    def create_pull_request(self, title: str, description: str):
        """
        Create a new Pull Request in a Git repository.

        Args:
            title (str): The title of the Pull Request.
            description (str): The description of the Pull Request.
        """
        return (
            f"Current branch {self.codebase.get_active_branch()}\n"
            + self.codebase.create_pull_request(pr_query=f"{title}\n {description}")
        )

    @action(name="ReadFile", stop=True, decorators=[traceable(run_type="tool")])
    def read_file(self, filepath: str):
        """
        Read a file.
        """
        return self.codebase.read_file(filepath)

    @action(
        "PlanAndImplementCodeChange",
        stop=False,
        decorators=[traceable(run_type="tool")],
    )
    def plan_code_change(self, input: str):
        """
        Plan and implement code changes based on a given description.
        """

        print(format_debug_msg(f"Planning code change: {input}"))

        context = gather_context(input, self.client, self.index, self.codebase)

        files = [
            file for file in self.codebase.list_files_in_bot_branch() if ".py" in file
        ]

        messages = [
            {
                "role": "user",
                "content": (
                    ""
                    + f"{context}\n"
                    + "<file_list>\n"
                    + "\n".join(files)
                    + "\n</file_list>\n"
                    + "<user_instruction>\n"
                    + f"{input}\n"
                    + "</user_instruction>\n"
                ),
            }
        ]

        print(format_debug_msg("Creating implementation plan, please wait..."))
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

        print(
            format_debug_msg(
                f"Implementation plan created: {implementation_plan.pretty_print()}"
            )
        )
        messages = implementation_plan.execute(self.client, self.index, self.codebase)

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
I've modified and updated the codebase according to your request in {self.codebase.get_active_branch()} branch. Here's what I've done:
- New files created: {files_created}
- Existing files updated: {files_updated}
- Problems encountered: {problems}

Is there anything else I can help you with?
"""

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
