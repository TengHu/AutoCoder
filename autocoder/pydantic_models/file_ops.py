import os
from typing import List

from actionweaver.actions.factories.pydantic_model_to_action import action_from_model
from pydantic import BaseModel, Field

from autocoder.pydantic_models.code_block_ops import create_blocks, create_code
from autocoder.pydantic_models.context import gather_context
from autocoder.telemetry import traceable
from autocoder.utils import bright_cyan, format_debug_msg

assert os.environ["MODEL"]
MODEL = os.environ["MODEL"]








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
        description="A list of code block modifications to be performed.",
    )
    file_creations: List[FileCreation] = Field(
        default=[],
        description="A list of file creation operations to be performed.",
    )

    @traceable(name="execute_implementation_plan", run_type="tool")
    def execute(self, openai_client, index, codebase) -> str:
        response = []
        for operation in self.file_creations:
            response.append(operation.execute(openai_client, codebase, index))

        for operation in self.file_modifications:
            response.append(operation.execute(openai_client, codebase))

        return response

    def pretty_print(self) -> str:
        return (
            f"{self.actions_to_take_on_codebase}\n"
            + "\n".join(
                [
                    f"{bright_cyan(op.file_path)}:{op.detailed_instruction_to_do_with_old_code}\n"
                    for op in self.file_modifications
                ]
            )
            + "\n".join(
                [
                    f"{bright_cyan(op.file_path)}:{op.detailed_instruction_what_to_write_to_the_file}\n"
                    for op in self.file_creations
                ]
            )
        )


CREATE_IMPLEMENTATION_PROMPT = """
Extract essential details to create a implementation plan and implement it, you can modify existing files or create new files.
Return an mapping from `implementationplan` to the plan object.
"""
create_implementation_plan = action_from_model(
    ImplementationPlan,
    name="ImplementationPlan",
    description=CREATE_IMPLEMENTATION_PROMPT,
    stop=True,
    decorators=[traceable(name="create_implementation_plan", run_type="tool")],
)
