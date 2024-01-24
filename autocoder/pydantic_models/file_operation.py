class FileOperation(BaseModel):
    """
    Represents a generic file operation.
    """

    file_path: str = Field(
        ..., description="The path to the file that will be operated on, e.g. file.py."
    )

import os
from pydantic import BaseModel, Field

assert os.environ["MODEL"]
MODEL = os.environ["MODEL"]
