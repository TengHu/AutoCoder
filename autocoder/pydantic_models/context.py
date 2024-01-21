import os
from collections import defaultdict
from typing import List

from actionweaver.actions.factories.pydantic_model_to_action import action_from_model
from pydantic import BaseModel, Field

from autocoder.telemetry import traceable

assert os.environ["MODEL"]
MODEL = os.environ["MODEL"]


class Context(BaseModel):
    what_to_do: str = Field(..., description="The task to be performed.")
    codebase_query: List[str] = Field(
        default=[],
        description="List of queries used to extract information from the codebase relevant to the task.",
    )
    files_mentioned_in_instruction: List[str] = Field(
        default=[], description="List of files mentioned in the instruction"
    )


@traceable(run_type="tool")
def gather_context(input, llm_client, index, codebase) -> str:
    user_prompt = input

    messages = [
        {
            "role": "user",
            "content": user_prompt,
        },
    ]
    context = create_context.invoke(
        llm_client,
        messages=messages,
        model=MODEL,
        stream=False,
        force=True,
    )

    if isinstance(context, list):
        context = context[0]

    results = defaultdict(list)

    for query in context.codebase_query + [context.what_to_do]:
        nodes = index.query(query)
        for node in nodes:
            results[node.file_path].append(
                {
                    "file_path": node.file_path,
                    "length": node.end_char_idx - node.start_char_idx,
                    "content": node.content,
                }
            )

    valid_files = set(codebase.list_files_in_main_branch())
    files_response = codebase.read_files(
        [file for file in context.files_mentioned_in_instruction if file in valid_files]
    )
    for file, content in files_response.items():
        results[file] = [
            {
                "file_path": file,
                "length": len(content),
                "content": content,
            }
        ]

    nodes = [node for _, v in results.items() for node in v]
    nodes.sort(key=lambda x: x["length"], reverse=True)

    return (
        "<context>:\n"
        + "\n".join(
            [
                f"<snippet {node['file_path']}>\n{node['content']}\n</snippet {node['file_path']}>"
                for node in nodes
            ]
        )
        + "</context>"
    )


CREATE_CONTEXT_PROMPT = "Extract essential details to request more context"

create_context = action_from_model(
    Context,
    name="Context",
    description=CREATE_CONTEXT_PROMPT,
    stop=True,
    decorators=[traceable(name="create_context_model", run_type="tool")],
)
