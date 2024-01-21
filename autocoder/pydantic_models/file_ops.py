import os
from typing import List

from actionweaver.actions.factories.pydantic_model_to_action import action_from_model
from pydantic import BaseModel, Field

from autocoder.pydantic_models.code_block_ops import create_blocks
from autocoder.telemetry import traceable

assert os.environ["MODEL"]
MODEL = os.environ["MODEL"]



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
