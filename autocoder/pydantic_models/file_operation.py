class FileOperation(BaseModel):
    """
    Represents a generic file operation.
    """

    file_path: str = Field(
        ..., description="The path to the file that will be operated on, e.g. file.py."
    )
