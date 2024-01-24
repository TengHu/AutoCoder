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
        # Function body omitted for brevity
        pass