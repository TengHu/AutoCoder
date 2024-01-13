from typing import List, Union

from actionweaver.actions.factories.pydantic_model_to_action import action_from_model
from pydantic import BaseModel, Field


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
    def execute(self) -> str:
        """
        Perform the file creation operation and return a status message.
        """
        return github_api.create_file(file_query=f"{self.file_path}\n {self.content}")


class FileUpdate(FileOperation):
    """
    Represents an operation to update an existing file.
    """

    code_snippet_to_be_replaced: str = Field(
        ..., description="The code already exists, but it needs to be updated."
    )
    new_code_snippet: str = Field(
        ..., description="The new code to replace the old content"
    )

    @traceable(name="execute_file_update", run_type="tool")
    def execute(self) -> str:
        """
        Perform the file update operation and return a status message.
        """
        content = f"""{self.file_path}\nOLD <<<<\n{self.code_snippet_to_be_replaced}\n>>>> OLD\nNEW <<<<\n{self.new_code_snippet}\n >>>> NEW"""
        return github_api.update_file(content)


class BatchFileOperations(BaseModel):
    """
    Represents a collection of file operations to be applied.
    """

    file_creations: List[FileCreation] = Field(
        default=[],
        description="A list of file creation operations to be performed when creating new files.",
    )
    file_updates: List[FileUpdate] = Field(
        default=[],
        description="A list of file update operations to be performed when modifying existing files.",
    )

    @traceable(name="execute_batch_file_operations", run_type="tool")
    def execute_all(self) -> str:
        """
        Execute all operations in the batch.
        """
        response = []
        for operation in self.file_creations:
            response.append(operation.execute())

        for operation in self.file_updates:
            response.append(operation.execute())

        return response


PLAN_CODE_CHANGE_PROMPT = """Making a collection of file changes."""
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
    def execute(self, openai_client, context) -> str:
        user_msg = f"""
        {context}
        ############################## 
        Task Description: {self.description}
        Action Required: {self.action_required}"""
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
        return operations.execute_all()


class Tasks(BaseModel):
    chain_of_thought: str = Field(
        None, description="Think step by step to plan what tasks required."
    )
    tasks: List[Task]

    @traceable(name="execute_tasks", run_type="tool")
    def execute(self, openai_client, context) -> str:
        return [task.execute(openai_client, context) for task in self.tasks]


CREATE_TASKS_PROMPT = "Create a list of programming tasks, each task can be accomplished by modifying existing files or creating new ones"
create_tasks = action_from_model(
    Tasks,
    name="Tasks",
    description=CREATE_TASKS_PROMPT,
    stop=True,
    decorators=[traceable(run_type="tool")],
)


class Context(BaseModel):
    semantic_queries: List[str] = Field(
        default=[],
        description="List of semantic queries used to extract information from the codebase, encompassing elements such as function names, class names, import statements, variable names, and error messages, all relevant to the task.",
    )
    instructions: List[str] = Field(
        default=[], description="List of instructions relevant to the task."
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
