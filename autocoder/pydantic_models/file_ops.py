import os
from typing import List

from actionweaver.actions.factories.pydantic_model_to_action import action_from_model
from pydantic import BaseModel, Field

from autocoder.pydantic_models.code_block_ops import create_blocks, create_code
from autocoder.pydantic_models.context import gather_context
from autocoder.telemetry import traceable

assert os.environ["MODEL"]
MODEL = os.environ["MODEL"]





class FileCreation(FileOperation):
    """
    Represents an operation to create a new file.
    """

    detailed_instruction_what_to_write_to_the_file: str = Field(
        ..., description="The detailed instruction what to write to the file."
    )

    @traceable(
        name="execute_file_creation",
        run_type="tool",
    )
    def execute(self, openai_client, codebase, index) -> str:
        input = (
            "<file>\n"
            + f"{self.file_path}\n"
            + "</file>\n"
            + "<user_instruction>\n"
            + f"{self.detailed_instruction_what_to_write_to_the_file}\n"
            + "</user_instruction>\n"
        )

        context = gather_context(
            input=input,
            llm_client=openai_client,
            index=index,
            codebase=codebase,
        )
        messages = [
            {
                "role": "user",
                "content": (
                    f"{context}\n"
                    + f"<action_related_to_what_to_add_to_file: {self.file_path}>\n"
                    + f"{self.detailed_instruction_what_to_write_to_the_file}\n"
                    + f"</action_related_to_what_to_add_to_file: {self.file_path}>\n"
                ),
            },
        ]
        snippet = create_code.invoke(
            openai_client,
            messages=messages,
            model=MODEL,
            stream=False,
            force=True,
        )

        if isinstance(snippet, list):
            snippet = snippet[0]
        return codebase.create_file(file_query=f"{self.file_path}\n {snippet.code}")


class ImplementationPlan(BaseModel):
    """
    This class represents a plan for implementing a feature.
    """

    actions_to_take_on_codebase: str = Field(
        ...,
        description="A list of actions to take on the codebase.",
    )

    file_modifications: List[FileModification] = Field(
        default=[],
        description="A list of file modifications to be performed.",
    )
    file_creations: List[FileCreation] = Field(
        
