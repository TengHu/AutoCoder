import os
from typing import List

from actionweaver.actions.factories.pydantic_model_to_action import action_from_model
from pydantic import BaseModel, Field
from telemetry import traceable

assert os.environ["MODEL"]
MODEL = os.environ["MODEL"]


class FileOperation(BaseModel):
    """
    Represents a generic file operation.
    """

    file_path: str = Field(
        ..., description="The path to the file that will be operated on."
    )


class FileModification(FileOperation):
    """
    Represents a file modification operation, which include a rewritten_instruction and blocks_operations.
    """

    rewritten_instruction: str = Field(
        ..., description="A more detailed instruction of the what you plan to do."
    )

    @traceable(name="execute_file_modification", run_type="tool")
    def execute(self, openai_client, github_api, codebase, context) -> str:
        file_content = codebase.read_file(self.file_path)
        messages = [
            {
                "role": "user",
                "content": (
                    f"{context} \n"
                    + f"<START OF FILE CONTENT {self.file_path}>\n"
                    + f"<END OF CONTENT {file_content}>\n"
                    + f"<START OF INSTRUCTION>\n"
                    + self.rewritten_instruction
                ),
            },
        ]
        blocks = create_blocks.invoke(
            openai_client,
            messages=messages,
            model=MODEL,
            stream=False,
            force=True,
        )

        if isinstance(blocks, list):
            blocks = blocks[0]

        unique_block_ops = {
            block_op.calculate_hash(): block_op for block_op in blocks.operations
        }

        # unique_block_ops = {
        #     block_op.calculate_hash(): block_op for block_op in self.blocks_operations
        # }
        unique_block_ops_list = list(unique_block_ops.values())

        return [
            block.execute(self.file_path, openai_client, github_api, codebase)
            for block in unique_block_ops_list
        ]


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


class ImplementationPlan(BaseModel):
    """
    This class represents a plan for implementing a feature.
    """

    thoughts: str = Field(
        ...,
        description="Carefully consider and plan the necessary actions, such as which files need modification and which files need creation.",
    )

    file_modifications: List[FileModification] = Field(
        default=[],
        description="A list of file modifications to be performed.",
    )
    file_creations: List[FileCreation] = Field(
        default=[],
        description="A list of file creation operations to be performed.",
    )

    @traceable(name="execute_implementation_plan", run_type="tool")
    def execute(self, openai_client, github_api, context, codebase) -> str:
        response = []
        for operation in self.file_creations:
            response.append(operation.execute(github_api))

        for operation in self.file_modifications:
            response.append(
                operation.execute(openai_client, github_api, codebase, context)
            )

        return response


CREATE_IMPLEMENTATION_PROMPT = """
Extract essential details to create a implementation plan and implement it, return an mapping from key `implementationplan` to the value
"""
create_implementation_plan = action_from_model(
    ImplementationPlan,
    name="ImplementationPlan",
    description=CREATE_IMPLEMENTATION_PROMPT,
    stop=True,
    decorators=[traceable(run_type="tool")],
)
