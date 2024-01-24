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

        context = gather_context(
            input=input,
            llm_client=openai_client,
            index=index,
            codebase=codebase,
            add_line_index=True,
        )
        messages = [
            {
                "role": "user",
                "content": (
                    f"{context}\n"
                    + f"<action_related_to_content_in: {self.file_path}>\n"
                    + f"{self.detailed_instruction_to_do_with_old_code}\n"
                    + f"</action_related_to_content_in: {self.file_path}>\n"
                ),
            },
        ]
        blocks = create_blocks.invoke(
            openai_client,
            messages=messages,
            model=MODEL,
            stream=False,
            force=True,
        )

        if isinstance(blocks, list):
            blocks = blocks[0]

        unique_block_ops = {
            block_op.calculate_hash(): block_op for block_op in blocks.operations
        }

        unique_block_ops_list = list(unique_block_ops.values())

        return [
            block.execute(self.file_path, openai_client, codebase)
            for block in unique_block_ops_list
        ]