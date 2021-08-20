from typing import List
import subprocess


def get_branch_head() -> str:
    # this returns "origin/main" or "origin/master" - pull out just the last bit
    return (
        subprocess.check_output("git rev-parse --abbrev-ref origin/HEAD".split())
        .decode()
        .strip()
        .split("/")[1]
    )


def break_large_message(text: str, break_at: int = 4000) -> List:
    """
    Slack messages must be less than 4000 characters.

    This breaks large strings into a list of sections that are each
    less than 4000 characters.
    """
    chunks = []
    temp = []
    text = text.split("\n")
    count = 0

    for line in text:
        print(count, len(line))
        if len(line) + count < break_at:
            count += len(line)
            temp.append(line)
        else:
            chunks.append("\n".join(temp))
            temp = []
            count = 0
            count += len(line)
            temp.append(line)

    # tack on any leftovers
    chunks.append("\n".join(temp))
    return chunks
