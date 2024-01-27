import os
from typing import List

from actionweaver.actions.factories.pydantic_model_to_action import action_from_model
from pydantic import BaseModel, Field

from autocoder.telemetry import traceable
from autocoder.utils import colored_diff, format_debug_msg

assert os.environ["MODEL"]
MODEL = os.environ["MODEL"]


# class BlockOp(BaseModel):
#     """Represents a replacement for a continuous code block.
#     If the goal is to delete a code block, you can achieve it by setting the new_code to an empty string.
#     If the goal is to insert a code block, you can do so by setting the start_line_old_block and end_line_old_block to the same line before or after the code block.
#     """

#     start_line_old_block: str = Field(
#         ...,
#         description="The entire first line of the original code block (before newline).",
#     )

#     end_line_old_block: str = Field(
#         ...,
#         description="The entire last line of the original code block (before newline).",
#     )
#     new_code: str = Field(
#         ..., description="The new code to replace the original content."
#     )

#     def calculate_hash(self):
#         """
#         Calculate a hash value for the BlockOp instance.
#         """
#         import hashlib

#         # Convert the BlockOp instance to a string representation
#         block_op_str = f"{self.first_line_of_original_block}{self.last_line_of_original_block}{self.new_code}"

#         # Create a hash object and update it with the string representation
#         hash_obj = hashlib.md5(block_op_str.encode())

#         # Return the hexadecimal digest of the hash
#         return hash_obj.hexdigest()

#     def find_block(self, content, cutoff=0.7):
#         import difflib

#         content = content.split("\n")

#         # remove junk character
#         sanitized_content = [line.replace("  ", "") for line in content]

#         match_start_line = difflib.get_close_matches(
#             self.first_line_of_original_block,
#             sanitized_content,
#             n=3,
#             cutoff=cutoff,
#         )

#         # in case fuzzy matching fails
#         if not match_start_line:
#             return None
#         else:
#             match_start_line = match_start_line[0]

#         start_line_index = sanitized_content.index(match_start_line)

#         match_end_line = difflib.get_close_matches(
#             self.last_line_of_original_block,
#             sanitized_content[start_line_index:],
#             n=3,
#             cutoff=cutoff,
#         )

#         # in case fuzzy matching fails
#         if not match_end_line:
#             return None
#         else:
#             match_end_line = match_end_line[0]

#         match_end_index = start_line_index + sanitized_content[start_line_index:].index(
#             match_end_line
#         )

#         return "\n".join(content[start_line_index : match_end_index + 1])

#     @traceable(name="execute_block_operation", run_type="tool")
#     def execute(self, file_path, openai_client, github_api, codebase) -> str:
#         existing_code_block = self.find_block(codebase.read_file(file_path))

#         if not existing_code_block:
#             return f"Failed to find the code block from `{self.start_line_old_block}` to `{self.end_line_old_block}` in {file_path}."

#         new_code_block = self.new_code

#         content = f"""{file_path}\nOLD <<<<\n{existing_code_block}\n>>>> OLD\nNEW <<<<\n{new_code_block}\n >>>> NEW"""

#         response = ""
#         try:
#             response = github_api.update_file(content)
#         except Exception as e:
#             response = f"Failed to update file {file_path} to replace old content {existing_code_block} with {new_code_block}. Original Exception: {e}."
#         return response


class BlockOpOnLineIdx(BaseModel):
    """Represents a replacement for a continuous code block.
    If the goal is to delete a code block, you can do so by setting the start_line_idx and end_line_idx to the code block you want to delete.
    If the goal is to insert a code block, you can do so by setting the start_line_idx and end_line_idx to the same line before or after you want to insert the code.

    Code block MUST be completed in terms of function, class, or if/else statement.
    """

    # first_line_of_original_block: str = Field(
    #     ...,
    #     description="The first line of the original code block, (everything between newlines) including whitespaces.",
    # )
    # last_line_of_original_block: str = Field(
    #     ...,
    #     description="The last line of the original code block, (everything between newlines) including whitespaces.",
    # )

    file_path: str = Field(..., description="The path to the file that will be changed")

    start_line_idx: int = Field(
        ...,
        description="The line index of the first line of the original code block.",
    )

    end_line_idx: int = Field(
        ...,
        description="The line index of the last line of the original code block.",
    )

    # The `instruction_to_rewrite_code_block` field in the `BlockOpOnLineIdx` class represents the
    # instruction to rewrite the code block. It provides guidance on how the code block should be
    # modified or replaced. This instruction can include information on what changes should be made,
    # what code should be added or removed, and any other specific instructions for rewriting the code
    # block.
    instruction_to_rewrite_code_block: str = Field(
        ...,
        description="The instruction to rewrite the code block.",
    )

    # new_code: str = Field(
    #     ...,
    #     description="The new code to replace the original content. Each  line follows the same indentation pattern as old code",
    # )

    def calculate_hash(self):
        """
        Calculate a hash value for the BlockOp instance.
        """
        import hashlib

        # Convert the BlockOp instance to a string representation
        block_op_str = f"{self.file_path}{self.start_line_idx}{self.end_line_idx}"

        # Create a hash object and update it with the string representation
        hash_obj = hashlib.md5(block_op_str.encode())

        # Return the hexadecimal digest of the hash
        return hash_obj.hexdigest()

    def find_block(self, content):
        content = content.split("\n")
        return "\n".join(content[self.start_line_idx : self.end_line_idx + 1])

    @traceable(name="create_block_update", run_type="tool")
    def create_block_update(self, openai_client, codebase) -> str:
        file_content = codebase.read_file(self.file_path)
        if not file_content:
            return f"{self.file_path} doesn't exist"

        existing_code_block = self.find_block(file_content)
        if not existing_code_block:
            return f"Failed to find the code block in {self.file_path}."

        messages = [
            {
                "role": "system",
                "content": "Modify old code block based on the instruction and return in JSON. Add the leading whitespace to the new code block the same as the old code block.",
            },
            {
                "role": "user",
                "content": (
                    "<old_code_block>\n"
                    + f"{existing_code_block}\n"
                    + "</old_code_block>\n"
                    + f"<instruction_to_rewrite_the_code_block>\n"
                    + f"{self.instruction_to_rewrite_code_block}\n"
                    + "</instruction_to_rewrite_the_code_block>\n"
                ),
            },
        ]
        snippet = create_code.invoke(
            openai_client,
            messages=messages,
            model=MODEL,
            temperature=0.0,
            stream=False,
            force=True,
        )

        if isinstance(snippet, list):
            snippet = snippet[0]

        new_code_block = snippet.code

        print(format_debug_msg(f"Committing code change to {self.file_path}"))
        print(colored_diff(existing_code_block, new_code_block))

        return f"""{self.file_path}\nOLD <<<<\n{existing_code_block}\n>>>> OLD\nNEW <<<<\n{new_code_block}\n>>>> NEW"""


class BlockOperations(BaseModel):
    """
    Represents a collection of operations on code blocks within a file. Code blocks are not overlapping.
    """

    operations: List[BlockOpOnLineIdx] = Field(
        ...,
        description="A list of code block operations within the file.",
    )


CREATE_BLOCKS_PROMPT = "Extract and rewrite code blocks of interest within a file."
create_blocks = action_from_model(
    BlockOperations,
    name="BlockOperations",
    description=CREATE_BLOCKS_PROMPT,
    stop=True,
    decorators=[traceable(name="create_block_operations", run_type="tool")],
)


class CodeSnippet(BaseModel):
    """
    Represents a code block.
    """

    code: str = Field(
        ...,
        description="The code block.",
    )


CREATE_CODE_PROMPT = "Rewrite code block"
create_code = action_from_model(
    CodeSnippet,
    name="CodeSnippet",
    description=CREATE_CODE_PROMPT,
    stop=True,
    decorators=[traceable(name="create_code", run_type="tool")],
)
