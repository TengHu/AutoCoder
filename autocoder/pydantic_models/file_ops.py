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












