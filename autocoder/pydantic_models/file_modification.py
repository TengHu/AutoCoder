class FileModification(FileOperation):
    """
    Represents a file modification operation
    """

    detailed_instruction_to_do_with_old_code: str = Field(
        ..., description="The detailed instruction to do with the old code."
    )

    @traceable(name="execute_file_modification", run_type="tool")
    def execute(self, openai_client, codebase, index) -> str:
        input = (
            "<file>\n"
            + f"{self.file_path}\n"
            + "</file>\n"
            + "<user_instruction>\n"
            + f"{self.detailed_instruction_to_do_with_old_code}\n"
            + "</user_instruction>\n"
        )

        # [Rest of the implementation...]