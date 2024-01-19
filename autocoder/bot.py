import datetime
import os
import uuid
from typing import List, Union

from actionweaver import action
from actionweaver.utils.tokens import TokenUsageTracker
from langchain_community.utilities.github import GitHubAPIWrapper
from langsmith.run_helpers import traceable
from llama_index import Document, ServiceContext, VectorStoreIndex
from llama_index.node_parser import CodeSplitter
from anthropic import AzureAnthropicAI, AnthropicAI
from pydantic import BaseModel, Field

from autocoder.pydantic_models import create_context, create_tasks
from autocoder.telemetry import trace_client

assert os.environ["MODEL"]
MODEL = os.environ["MODEL"]


DIVIDING_LINE = """
###############
This section is divider and not a part of the code.
{input}
#############

"""


class AutoCoder:
    def __init__(self, github_api, index):
        self.github_api = github_api

        self.client = trace_client(AzureAnthropicAI(
        anthropic_endpoint = os.getenv("ANTHROPIC_OPENAI_ENDPOINT"),
        api_key=os.getenv("ANTHROPIC_OPENAI_KEY"),
        api_version="2023-10-01-preview"
    ))
        # ))
        self.client = trace_client(AnthropicAI())
        self.messages = [
            {
                "role": "system",
                "content": "You are a coding assistant, you have the capability to assist with code-related tasks and modify files.",
            },
        ]
        self.index = index

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
                self.plan_code_change.name: None,
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

    @traceable(run_type="tool")
    def gather_context(self, input):
        user_prompt = input

        messages = [
            # {
            #     "role": "system",
            #     "content": "You are good at extract information from description",
            # },
            {"role": "user", "content": f"Description: {user_prompt}"},
        ]
        context = create_context.invoke(
            self.client,
            messages=messages,
            model=MODEL,
            stream=False,
            force=True,
        )

        if isinstance(context, list):
            context = context[0]

        index_response = ""
        for query in context.queries + context.instructions:
            nodes = self.index.query(query)
            for node in nodes:
                index_response = (
                    index_response
                    + DIVIDING_LINE.format(
                        input=f"Code Snippet From Filepath: {node.metadata['file']}"
                    )
                    + f"{node.text}\n"
                    + "<END OF SNIPPET>"
                )

        file_response = self.read_files(context.files)
        code_search_response = self.search_code(" ".join(context.code_snippets))

        return (
            "CONTEXT FOR MAKING CODE MODIFICATIONS:\n"
            + index_response
            + "\n"
            + file_response
            + "\n"
            + code_search_response
        )

    @action(name="QuestionAnswer", decorators=[traceable(run_type="tool")])
    def question_answer(self, rewritten_query: str, keywords: List[str]):
        """Answer questions about the codebase"""

        context = self.gather_context(" ".join(keywords))

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
        return self.github_api.create_pull_request(pr_query=f"{title}\n {description}")

    @traceable(run_type="tool")
    def read_files(self, files: List[str]) -> List[str]:
        """
        Read the content of multiple files in the GitHub repo

        Args:
            files (List[str]): A list of file paths to be read using the GitHub API.
        """
        response = ""
        for file in files:
            api_response = self.github_api.read_file(file)
            if f"File not found `{file}`" not in api_response:
                response = (
                    response
                    + DIVIDING_LINE.format(input=f"Content From Filepath: {file}")
                    + f"{self.github_api.read_file(file)}\n<END OF FILE>"
                )
        return response

    def rephrase(self, input: str):
        messages = [{"role": "user", "content": f"{input}\n####\nRephrase"}]
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

    @action("PlanCodeChange", stop=True, decorators=[traceable(run_type="tool")])
    def plan_code_change(self, description: str):
        """
        Plan code changes based on a given description.

        This method is designed to handle various types of code alterations such as
        inserting new code, refactoring existing code, replacing segments, or making
        general modifications.
        """
        context = self.gather_context(description)

        user_prompt = f"""
        {context}
        {'#' * 20}
        Description:
        {description}"""

        messages = [{"role": "user", "content": user_prompt}]
        tasks = create_tasks.invoke(
            self.client,
            messages=messages,
            temperature=0.1,
            model=MODEL,
            stream=False,
            force=True,
        )

        if isinstance(tasks, list):
            tasks = tasks[0]
        messages = tasks.execute(self.client, self.github_api, context)

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

        return self.rephrase(
            f"""
- New files created: {files_created}
- Existing files updated: {files_updated}
- Problems encountered: {problems}
"""
        )

    def search_code(self, query: str):
        return self.github_api.search_code(query)
