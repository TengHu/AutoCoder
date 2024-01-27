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
        input = (
            "<file>\n"
            + f"{self.file_path}\n"
            + "</file>\n"
            + "<user_instruction>\n"
            + f"{self.detailed_instruction_what_to_write_to_the_file}\n"
            + "</user_instruction>\n"
        )

        print(format_debug_msg(f"Creating file: {self.file_path}"))

        context = gather_context(
            input=input,
            llm_client=openai_client,
            index=index,
            codebase=codebase,
        )
        messages = [
            {
                "role": "user",
                "content": (
                    f"{context}\n"
                    + f"<action_related_to_what_to_add_to_file: {self.file_path}>\n"
                    + f"{self.detailed_instruction_what_to_write_to_the_file}\n"
                    + f"</action_related_to_what_to_add_to_file: {self.file_path}>\n"
                ),
            },
        ]
        snippet = create_code.invoke(
            openai_client,
            messages=messages,
            model=MODEL,
            stream=False,
            force=True,
        )

        if isinstance(snippet, list):
            snippet = snippet[0]
        return codebase.create_file(file_query=f"{self.file_path}\n {snippet.code}")