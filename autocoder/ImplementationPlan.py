from typing import List
from pydantic import BaseModel, Field
from autocoder.pydantic_models.file_ops import FileModification, FileCreation
from autocoder.telemetry import traceable

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
        default=[],
        description="A list of file creation operations to be performed.",
    )

    @traceable(name="execute_implementation_plan", run_type="tool")
    def execute(self, openai_client, index, codebase) -> str:
        response = []
        for operation in self.file_creations:
            response.append(operation.execute(openai_client, codebase, index))

        for operation in self.file_modifications:
            response.append(operation.execute(openai_client, codebase, index))

        return response
