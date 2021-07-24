import subprocess


def get_branch_head() -> str:
    # this returns "origin/main" or "origin/master" - pull out just the last bit
    return (
        subprocess.check_output(
            "git rev-parse --abbrev-ref origin/HEAD".split()
        ).decode().strip().split('/')[1]
    )
