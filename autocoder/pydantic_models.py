import os
from typing import List, Union

from actionweaver.actions.factories.pydantic_model_to_action1 import action1_from_model
from langsmith.run_helpers import traceable
from pydantic import BaseModel, Field

assert os.environ["MODEL"]
MODEL = os.environ["MODEL"]


class FileOperation(BaseModel):
    """
    Represents a generic file operation.
    """

    description: str = Field(
        ..., description="A brief description of the file operation."
    )
    file_path: str = Field(
        ..., description="The path to the file that will be operated on."
    )


class FileCreation(FileOperation):
    """
    Represents an operation to create a new file.
    """

    content: str = Field(..., description="The content to be written to the file.")

    @traceable(
        name="execute_file_creation",
        run_type="tool",
    )
    def execute(self, github_api) -> str:
        """
        Perform the file creation operation and return a status message.
        """
        return github_api.create_file(file_query=f"{self.file_path}\n {self.content}")


class RewriteCode(FileOperation):
    """
    Represents an operation to rewrite code in an existing file.
    """

    existing_code: str = Field(..., description="The code that needs to be updated.")
    new_code: str = Field(..., description="The new code to replace the old content.")

    @traceable(name="execute_file_update", run_type="tool")
    def execute(self, github_api) -> str:
        """
        Perform the file update operation and return a status message.
        """
        content = f"""{self.file_path}\nOLD <<<<\n{self.existing_code}\n>>>> OLD\nNEW <<<<\n{self.new_code}\n >>>> NEW"""
        return github_api.update_file(content)


class BatchFileOperations(BaseModel):
    """
    Represents a collection of file operations to be applied.
    """

    new_file_creations: List[FileCreation] = Field(
        default=[],
        description="A list of file creation operations to be performed when creating new files.",
    )
    rewrite_existing_code: List[RewriteCode] = Field(
        default=[],
        description="A list of file update operations to be performed when modifying existing files.",
    )

    @traceable(name="execute_batch_file_operations", run_type="tool")
    def execute_all(self, github_api) -> str:
        """
        Execute all operations in the batch.
        """
        response = []
        for operation in self.new_file_creations:
            response.append(operation.execute(github_api))

        for operation in self.rewrite_existing_code:
            response.append(operation.execute(github_api))

        return response


PLAN_CODE_CHANGE_PROMPT = """Creating a compilation of code modifications, which includes both the creation of new files and the revision of existing code."""
batch_file_operations = action_from_model(
    BatchFileOperations,
    name="BatchFileOperations",
    description=PLAN_CODE_CHANGE_PROMPT,
    stop=True,
    decorators=[traceable(run_type="tool")],
)


class Task(BaseModel):
    """
    Task to be executed.
    """

    description: str = Field(..., description="Comprehensive details of the task.")

    action_required: str = Field(
        ...,
        description="a specific action needed to finish the task without using an external tool",
    )

    @traceable(name="execute_task", run_type="tool")
    def execute(self, openai_client, github_api, context) -> str:
        user_msg = f"""
        {context}
        {'#' * 20}
        [Task Description]: {self.description}
        [Action]: {self.action_required}"""
        messages = [{"role": "user", "content": user_msg}]

        operations = batch_file_operations.invoke(
            openai_client,
            messages=messages,
            temperature=0.1,
            model=MODEL,
            stream=False,
            force=True,
        )
        if isinstance(operations, list):
            operations = operations[0]
        return operations.execute_all(github_api)


class TaskPlan(BaseModel):
    chain_of_thought: str = Field(
        None, description="Think step by step to plan what coding tasks required."
    )
    tasks: List[Task]

    @traceable(name="execute_tasks", run_type="tool")
    def execute(self, openai_client, github_api, context) -> str:
        return [task.execute(openai_client, github_api, context) for task in self.tasks]


CREATE_TASKS_PROMPT = "Create a list of coding tasks, each task can be accomplished by modifying existing files or creating new ones"
create_tasks = action_from_model(
    TaskPlan,
    name="TaskPlan",
    description=CREATE_TASKS_PROMPT,
    stop=True,
    decorators=[traceable(run_type="tool")],
)


class Context(BaseModel):
    instructions: List[str] = Field(
        default=[], description="Instructions relevant to the task."
    )
    queries: List[str] = Field(
        default=[],
        description="List of queries used to extract information from the codebase, encompassing elements such as function names, class names, import statements, variable names, and error messages, all relevant to the task.",
    )
    code_snippets: List[str] = Field(
        default=[],
        description="Search for the code within the codebase.",
    )
    files: List[str] = Field(default=[], description="List of files, e.g. *.py")


CREATE_CONTEXT_PROMPT = "Extract essential details to request more context"
create_context = action_from_model(
    Context,
    name="Context",
    description=CREATE_CONTEXT_PROMPT,
    stop=True,
    decorators=[traceable(run_type="tool")],
)

DIVIDING_LINE = """
###############
This section is divider and not a part of the code.
# {input}
#############
"""
