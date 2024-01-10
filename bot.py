import os
from typing import List, Union
from langchain_community.utilities.github import GitHubAPIWrapper
from llama_index import Document, VectorStoreIndex, ServiceContext
from llama_index.node_parser import CodeSplitter
from actionweaver.utils.tokens import TokenUsageTracker
from openai import OpenAI, AzureOpenAI
from actionweaver import action
from actionweaver.actions.factories.pydantic_model_to_action import action_from_model
from pydantic import BaseModel, Field
import uuid
import datetime
from pydantic import BaseModel
from typing import List, Union
class AutoCoder:
    def __init__(self, github_api, index):
        self.github_api = github_api
        
        # self.client = trace_client(AzureOpenAI(
        #     azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"), 
        #     api_key=os.getenv("AZURE_OPENAI_KEY"),  
        #     api_version="2023-10-01-preview"
        # ))
        self.client = trace_client(OpenAI())
        self.messages = [
            {"role": "system", "content": "You are a helpful assistant."},
        ]
        self.index = index

        self.plan_and_execute_code_change = action_from_model(BatchFileOperations, name="BatchFileOperations", description="Making a collection of file changes", stop=True, decorators=[traceable(run_type="tool")])
        
        # TODO: think about user work flow, make this better
        # self.create_branch(f"aw_demo_bot_{str(datetime.datetime.now())[:10]}")
        self.create_branch(f"aw_demo_bot")


    def __call__(self, input: str):
        self.messages.append({"role": "user", "content": input})
        
        response = self.client.chat.completions.create(
          model=MODEL,
          messages=self.messages,
          stream=False,
          actions = [self.get_issues, self.question_answer, self.create_pull_request, self.make_code_change],
          token_usage_tracker = TokenUsageTracker(500),
        )

        content = response.choices[0].message.content
        self.messages.append({"role": "assistant", "content": content})
        return content

    @traceable(run_type="tool")
    def gather_context(self, input):
        nodes = self.index.query(input)

        context = ""
        for node in nodes:
            context += f"\n{'#' * 10} File: {node.metadata['file']}: \n{node.text}"
        return context
        

    @action(name="QuestionAnswer", decorators=[traceable(run_type="tool")])
    def question_answer(self, rewritten_query: str, keywords: List[str]):
        """Answer questions about the codebase"""

        context = self.gather_context(' '.join(keywords))
        
        messages = [{"role": "user", "content": f"{context}\n Question: {rewritten_query}"}]
        response = self.client.chat.completions.create(
              model=MODEL,
              messages=messages,
              stream=False,
              token_usage_tracker = TokenUsageTracker(500))
        return response

    @action(name="GetIssues", decorators=[traceable(run_type="tool")])
    def get_issues(self):
        """
        Get a list of issues from the GitHub repo.
        """
        response = self.github_api.get_issues()
        response = response.split('\n')
        return eval(response[1]) if len(response) > 1 else []

        
    @action(name="CreateGitBranch", decorators=[traceable(run_type="tool")])
    def create_branch(self, branch: str):
        """
        Create a new Git branch.
        """
        return github_api.create_branch(branch)
    
    @action(name="CreatePullRequest", decorators=[traceable(run_type="tool")])
    def create_pull_request(self, title: str, description: str):
        """
        Create a new Pull Request in a Git repository.
    
        Args:
            title (str): The title of the Pull Request.
            description (str): The description of the Pull Request.
        """
        return github_api.create_pull_request(pr_query=f'{title}\n{description}"')
    
    
    @action("MakeCodeChange", decorators=[traceable(run_type="tool")])
    def make_code_change(self, instruction: str):
        """
        Make code changes in one or more files.
        """

        context = self.gather_context(instruction)
        messages = [{"role": "user", "content": f"{context}\n#######\nInstruction: {instruction}"}]

        # return [BatchFileOperations]
        response = self.plan_and_execute_code_change.invoke(self.client, messages=messages, temperature=0.1, model=MODEL, stream=False, force=True)

        return response[0].execute_all()


    def search_code(self, query:str):
        return self.github_api.search_code(query)