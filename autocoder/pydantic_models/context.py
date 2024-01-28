import os
from collections import defaultdict
from typing import List

from actionweaver.actions.factories.pydantic_model_to_action import action_from_model
from pydantic import BaseModel, Field

from autocoder.telemetry import traceable
from autocoder.utils import format_debug_msg

assert os.environ["MODEL"]
MODEL = os.environ["MODEL"]


class Context(BaseModel):
    questions_to_ask: List[str] = Field(
        ...,
        description="List of questions to ask the codebase to gather more context",
    )

    file_name_mentioned_in_instruction: List[str] = Field(
        default=[],
        description="List of files mentioned in the instruction, e.g. file.py",
    )

    object_identifiers: List[str] = Field(
        default=[],
        description="List of identifiers mentioned in the instruction, e.g. class name, function name, variable name",
    )


@traceable(run_type="tool")
def gather_context(input, llm_client, index, codebase, add_line_index=False) -> str:
    user_prompt = input

    print(format_debug_msg("Gathering context, please wait..."))

    messages = [
        {
            "role": "user",
            "content": f"<info>\n`{user_prompt}`\n</info>\n<instruction>\nAnalyze the input above and extract information using ONLY the details in the input\n</instruction>",
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
    nodes = []
    for query in context.questions_to_ask + context.object_identifiers:
        print(format_debug_msg(f"Querying information about {query}"))
        nodes.extend(index.query(query))

    # Dedup nodes
    deduplicated_list = []
    unique_values = set()
    for n in nodes:
        if n.id not in unique_values:
            deduplicated_list.append(n)
            unique_values.add(n.id)
    nodes = deduplicated_list

    # parse nodes into jsons
    for node in nodes:
        results[node.file_path].append(
            {
                "file_path": node.file_path,
                "start_char_idx": node.start_char_idx,
                "end_char_idx": node.end_char_idx,
                "length": node.end_char_idx - node.start_char_idx,
                "content": node.content,
            }
        )

    valid_files = set(codebase.list_files_in_bot_branch())
    print(
        f"Reading files: {set(context.file_name_mentioned_in_instruction).intersection(valid_files)}"
    )
    files_response = codebase.read_files(
        [
            file
            for file in context.file_name_mentioned_in_instruction
            if file in valid_files
        ]
    )
    for file, content in files_response.items():
        results[file] = [
            {
                "file_path": file,
                "length": len(content),
                "start_char_idx": 0,
                "end_char_idx": len(content),
                "content": content,
            }
        ]

    nodes = [node for _, v in results.items() for node in v]
    nodes.sort(key=lambda x: (x["file_path"], -x["length"]))

    if add_line_index:
        for node in nodes:
            node["line_index"] = codebase.map_char_idx_to_line_idx(
                node["file_path"], node["start_char_idx"], node["end_char_idx"]
            )
            (
                content_lines,
                start_line_idx,
                end_line_idx,
            ) = codebase.map_char_idx_to_line_idx(
                node["file_path"],
                node["start_char_idx"],
                node["end_char_idx"],
            )

            node["content"] = "\n".join(
                [
                    f"{line_idx}. " + content_lines[line_idx]
                    for line_idx in range(start_line_idx, end_line_idx + 1)
                ]
            )
            node["start_line"] = start_line_idx
            node["end_line"] = end_line_idx

    return (
        "<context>:\n"
        + "\n".join(
            [
                f"<snippet {node['file_path']} start_line={node['start_line']} end_line={node['end_line']}>\n{node['content']}\n</snippet {node['file_path']}>"
                if add_line_index
                else f"<snippet {node['file_path']}>\n{node['content']}\n</snippet {node['file_path']}>"
                for node in nodes
            ]
        )
        + "\n</context>"
    )


CREATE_CONTEXT_PROMPT = "Extract essential details to request more context"

create_context = action_from_model(
    Context,
    name="Context",
    description=CREATE_CONTEXT_PROMPT,
    stop=True,
    decorators=[traceable(name="create_context_model", run_type="tool")],
)
