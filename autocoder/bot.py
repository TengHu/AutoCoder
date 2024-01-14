import datetime
import os
import uuid
from typing import List, Union

from openai import AzureOpenAI, OpenAI
from pydantic import BaseModel, Field

from actionweaver import action
from actionweaver.utils.tokens import TokenUsageTracker
from langchain_community.utilities.github import GitHubAPIWrapper
from langsmith.run_helpers import traceable
from llama_index import Document, ServiceContext, VectorStoreIndex
from llama_index.node_parser import CodeSplitter
from telemetry import trace_client

assert os.environ["MODEL"]
MODEL = os.environ["MODEL"]


class AutoCoder:
    """
    AutoCoder is a class responsible for automating coding tasks such as managing a codebase,
    answering questions, and planning code changes.
    
    Attributes:
        github_api (GitHubAPIWrapper): An instance of the GitHubAPIWrapper to interact with GitHub.
        index (VectorStoreIndex): An instance of VectorStoreIndex to perform semantic queries.
        client (OpenAI): An instance of OpenAI client to generate responses.
        messages (List[dict]): A list of messages that represent the conversation history.
    """
    def __init__(self, github_api, index):
        """
        Initializes the AutoCoder instance with the given GitHub API wrapper and index.

        Args:
            github_api (GitHubAPIWrapper): The GitHub API wrapper to interact with GitHub.
            index (VectorStoreIndex): The index to perform semantic queries.
        """
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
                "content": "You are an assistant tasked with managing a codebase. Think step-by-step and provide clear and comprehensive plans and answers",
            },
        ]
        self.index = index

        msg = self.create_branch(f"aw_demo_bot")
        print(f"[System] {msg}")

    def __call__(self, input: str):
        """
        Processes the input from the user and generates a response using the OpenAI client.

        Args:
            input (str): The input string from the user.

        Returns:
            str: The generated response from the assistant.
        """
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

        content = response.choices[0].message.content
        self.messages.append({"role": "assistant", "content": content})
        return content

    @traceable(run_type="tool")
    def gather_context(self, input):
        """
        Gathers context by extracting information from the user's description and performing semantic queries.

        Args:
            input (str): The user's description to extract information from.

        Returns:
            str: The combined responses from semantic queries and file readings.
        """
        user_prompt = input

        messages = [
            {
                "role": "system",
                "content": "You are good at extractubg information from description",
            },
            {"role": "user", "content": f"Description: {user_prompt}"},
        ]
        context = create_context.invoke(
            self.client,
            messages=messages,
            temperature=0.1,
            model=MODEL,
            stream=False,
            force=True,
        )

        if isinstance(context, list):
            context = context[0]

        index_response = ""
        for query in context.semantic_queries + context.instructions:
            nodes = self.index.query(query)
            for node in nodes:
                index_response = (
                    index_response
                    + DIVIDING_LINE.format(
                        input=f"Code Snippet From File: {node.metadata['file']}"
                    )
                    + f"{node.text}"
                )

        file_response = self.read_files(context.files)

        return index_response + "\n" + file_response

    @action(name="QuestionAnswer", decorators=[traceable(run_type="tool")])
    def question_answer(self, rewritten_query: str, keywords: List[str]):
        """
        Answers questions about the codebase by gathering context and querying the OpenAI client.

        Args:
            rewritten_query (str): The rewritten query to be answered.
            keywords (List[str]): A list of keywords related to the query.

        Returns:
            The response from the OpenAI client.
        """
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
        Retrieves a list of issues from the GitHub repository.

        Returns:
            A list of issues obtained from the GitHub API.
        """
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

    def read_files(self, files: List[str]) -> List[str]:
        """
        Read the content of multiple files in the GitHub repo

        Args:
            files (List[str]): A list of file paths to be read using the GitHub API.
        """
        response = ""
        for file in files:
            api_response = self.github_api.read_file(file)
            if "File not found" not in api_response:
                response = (
                    response
                    + DIVIDING_LINE.format(input=f"{file} full content:")
                    + f"{self.github_api.read_file(file)}\n"
                )
        return response

    @action("PlanCodeChange", decorators=[traceable(run_type="tool")])
    def plan_code_change(self, description: str):
        """
        Plan code changes based on a given description.

        This method is designed to handle various types of code alterations such as
        inserting new code, refactoring existing code, replacing segments, or making
        general modifications.

        Parameters:
        description (str): A detailed description of the code change required. This
                           should include the purpose of the change, the specific
                           areas of the codebase that are impacted, and any particular
                           requirements or constraints that need to be considered.

        need_more_context (bool): Flag indicating if additional context is needed for the task
        """
        context = self.gather_context(description)

        user_prompt = f"""
        {context}
        ########
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
        return tasks.execute(self.client, context)

    def search_code(self, query: str):
        return self.github_api.search_code(query)
