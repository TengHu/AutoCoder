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
