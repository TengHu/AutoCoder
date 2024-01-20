import os
from typing import List, Union

from actionweaver.actions.factories.pydantic_model_to_action import action_from_model
from langsmith.run_helpers import traceable
from pydantic import BaseModel, Field

assert os.environ["MODEL"]
MODEL = os.environ["MODEL"]


#### Code Block Operations ###


class BlockOp(BaseModel):
    """
    Represents a replacement to a continuous code block. If the intention is to remove the code block, simply set new_code to an empty string
    """

    start_line_old_block: str = Field(
        ...,
        description="The entire first line of the original code block (before newline).",
    )
    end_line_old_block: str = Field(
        ...,
        description="The entire last line of the original code block (before newline).",
    )
    new_code: str = Field(
        ..., description="The new code to replace the original content."
    )

    def calculate_hash(self):
        """
        Calculate a hash value for the BlockOp instance.
        """
        import hashlib

        # Convert the BlockOp instance to a string representation
        block_op_str = (
            f"{self.start_line_old_block}{self.end_line_old_block}{self.new_code}"
        )

        # Create a hash object and update it with the string representation
        hash_obj = hashlib.md5(block_op_str.encode())

        # Return the hexadecimal digest of the hash
        return hash_obj.hexdigest()

    def find_block(self, content, cutoff=0.7):
        import difflib

        content = content.split("\n")

        # remove junk character
        sanitized_content = [line.replace("  ", "") for line in content]

        match_start_line = difflib.get_close_matches(
            self.start_line_old_block,
            sanitized_content,
            n=3,
            cutoff=cutoff,
        )

        if not match_start_line:
            return None
        else:
            match_start_line = match_start_line[0]

        start_line_index = sanitized_content.index(match_start_line)

        match_end_line = difflib.get_close_matches(
            self.end_line_old_block,
            sanitized_content[start_line_index:],
            n=3,
            cutoff=cutoff,
        )[0]
        match_end_index = start_line_index + sanitized_content[start_line_index:].index(
            match_end_line
        )

        return "\n".join(content[start_line_index : match_end_index + 1])

    @traceable(name="execute_block_operation", run_type="tool")
    def execute(self, file_path, openai_client, github_api, codebase) -> str:
        existing_code_block = self.find_block(codebase.read_file(file_path))

        if not existing_code_block:
            return f"Failed to find the code block from `{self.start_line_old_block}` to `{self.end_line_old_block}` in {file_path}."

        new_code_block = self.new_code

        content = f"""{file_path}\nOLD <<<<\n{existing_code_block}\n>>>> OLD\nNEW <<<<\n{new_code_block}\n >>>> NEW"""

        response = ""
        try:
            response = github_api.update_file(content)
        except Exception as e:
            response = f"Failed to update file {file_path} to replace old content {existing_code_block} with {new_code_block}. Original Exception: {e}."
        return response


class BlockOperations(BaseModel):
    """
    Represents a collection of operations on code blocks within a file.
    """

    operations: List[BlockOp] = Field(
        ...,
        description="A list of code block operations within the file.",
    )


CREATE_BLOCKS_PROMPT = "Extract code blocks of interest within a file"
create_blocks = action_from_model(
    BlockOperations,
    name="BlockOperations",
    description=CREATE_BLOCKS_PROMPT,
    stop=True,
    decorators=[traceable(name="create_block_operations", run_type="tool")],
)

#### File Operations ###


class FileOperation(BaseModel):
    """
    Represents a generic file operation.
    """

    file_path: str = Field(
        ..., description="The path to the file that will be operated on."
    )


class FileModification(FileOperation):
    """
    Represents a file modification operation, which include a rewritten_instruction and blocks_operations.
    """

    rewritten_instruction: str = Field(
        ..., description="A more detailed instruction of the what you plan to do."
    )

    @traceable(name="execute_file_modification", run_type="tool")
    def execute(self, openai_client, github_api, codebase, context) -> str:
        file_content = codebase.read_file(self.file_path)
        messages = [
            {
                "role": "user",
                "content": (
                    f"{context} \n"
                    + f"<START OF FILE CONTENT {self.file_path}>\n"
                    + f"<END OF CONTENT {file_content}>\n"
                    + f"<START OF INSTRUCTION>\n"
                    + self.rewritten_instruction
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

        # unique_block_ops = {
        #     block_op.calculate_hash(): block_op for block_op in self.blocks_operations
        # }
        unique_block_ops_list = list(unique_block_ops.values())

        return [
            block.execute(self.file_path, openai_client, github_api, codebase)
            for block in unique_block_ops_list
        ]


class FileCreation(FileOperation):
    """
    Represents an operation to create a new file.
    """

    content: str = Field(..., description="The content to be written to the file.")

    @traceable(
        name="execute_file_creation",
        run_type="tool",
    )
    def execute(self, github_api) -> str:
        """
        Perform the file creation operation and return a status message.
        """
        return github_api.create_file(file_query=f"{self.file_path}\n {self.content}")


class ImplementationPlan(BaseModel):
    """
    This class represents a plan for implementing a feature.
    """

    thoughts: str = Field(
        ...,
        description="Carefully consider and plan the necessary actions, such as which files need modification and which files need creation.",
    )

    file_modifications: List[FileModification] = Field(
        default=[],
        description="A list of file modifications to be performed.",
    )
    file_creations: List[FileCreation] = Field(
        default=[],
        description="A list of file creation operations to be performed.",
    )

    @traceable(name="execute_implementation_plan", run_type="tool")
    def execute(self, openai_client, github_api, context, codebase) -> str:
        response = []
        for operation in self.file_creations:
            response.append(operation.execute(github_api))

        for operation in self.file_modifications:
            response.append(
                operation.execute(openai_client, github_api, codebase, context)
            )

        return response


CREATE_IMPLEMENTATION_PROMPT = """
Extract essential details to create a implementation plan and implement it, return an mapping from key `implementationplan` to the value
"""
create_implementation_plan = action_from_model(
    ImplementationPlan,
    name="ImplementationPlan",
    description=CREATE_IMPLEMENTATION_PROMPT,
    stop=True,
    decorators=[traceable(run_type="tool")],
)


###### Context ######
class Context(BaseModel):
    instruction: str = Field(..., description="Instructions relevant to the task.")
    queries: List[str] = Field(
        default=[],
        description="List of queries used to extract information from the codebase, encompassing elements such as function names, class names, import statements, variable names, and error messages, all relevant to the task.",
    )
    code_snippets: List[str] = Field(
        default=[],
        description="Search for the code within the codebase.",
    )
    files_mentioned_in_instruction: List[str] = Field(
        default=[], description="List of files mentioned in the instruction"
    )


CREATE_CONTEXT_PROMPT = "Extract essential details to request more context"
create_context = action_from_model(
    Context,
    name="Context",
    description=CREATE_CONTEXT_PROMPT,
    stop=True,
    decorators=[traceable(run_type="tool")],
)
