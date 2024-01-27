class FileModification(FileOperation):
    """Represents a file modification operation"""

    detailed_instruction_to_do_with_old_code: str = Field(
        ..., description='The detailed instruction to do with the old code.'
    )

    @traceable(name='execute_file_modification', run_type='tool')
    def execute(self, openai_client, codebase) -> str:
        print(format_debug_msg(f'Modifying file: {self.file_path}'))

        context = codebase.read_file(self.file_path, add_line_index=True)
        messages = [
            {
                'role': 'user',
                'content': (
                    f'<file {self.file_path}>
'
                    + f'{context}
'
                    + f'</file {self.file_path}>
'
                    + f'<action_related_to_codeblocks_in: {self.file_path}>
'
                    + f'{self.detailed_instruction_to_do_with_old_code}
'
                    + f'</action_related_to_codeblocks_in: {self.file_path}>
'
                    + 'identify the code blocks of interest, then rewrite them'
                ),
            },
        ]
        blocks = create_blocks.invoke(
            openai_client,
            messages=messages,
            model=MODEL,
            temperature=0.1,
            stream=False,
            force=True,
        )

        if isinstance(blocks, list):
            blocks = blocks[0]

        unique_block_ops = {
            block_op.calculate_hash(): block_op for block_op in blocks.operations
        }

        unique_block_ops_list = list(unique_block_ops.values())

        updates = [
            block.create_block_update(openai_client, codebase)
            for block in unique_block_ops_list
        ]

        return [codebase.update_file(update) for update in updates]