def format_debug_msg(msg: str) -> str:
    """
    Format a debug message to be printed to the console.
    """
    return light_green("[DEBUG] ") + msg


def bright_cyan(text):
    return f"\033[96m{text}\033[0m"


def light_green(text):
    return f"\033[92m{text}\033[0m"


def colored_diff(old_text: str, new_text: str) -> str:
    import difflib

    # Split the text into lines
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()

    # Create a differ object
    differ = difflib.Differ()

    # Compare the lines
    diff = list(differ.compare(old_lines, new_lines))

    res = []
    for line in diff:
        if line.startswith("+"):
            res.append("\033[32m" + line + "\033[0m")  # Green color for additions
        elif line.startswith("-"):
            res.append("\033[31m" + line + "\033[0m")  # Red color for deletions
        elif line.startswith("?"):
            continue
        else:
            res.append(line)

    return "\n".join(res)
