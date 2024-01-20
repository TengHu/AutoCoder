from typing import List

from actionweaver.actions.factories.pydantic_model_to_action import action_from_model
from pydantic import BaseModel, Field

from autocoder.telemetry import traceable


class Context(BaseModel):
    instruction: str = Field(..., description="Instructions relevant to the task.")
    queries: List[str] = Field(
        default=[],
        description="List of queries used to extract information from the codebase, encompassing elements such as function names, class names, import statements, variable names, and error messages, all relevant to the task.",
    )
    code_snippets: List[str] = Field(
        default=[],
        description="Search for the code within the codebase.",
    )
    files_mentioned_in_instruction: List[str] = Field(
        default=[], description="List of files mentioned in the instruction"
    )


CREATE_CONTEXT_PROMPT = "Extract essential details to request more context"

create_context = action_from_model(
    Context,
    name="Context",
    description=CREATE_CONTEXT_PROMPT,
    stop=True,
    decorators=[traceable(run_type="tool")],
)
