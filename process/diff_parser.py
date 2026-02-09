import subprocess

def get_diff_summary(commit_hash):
    diff = subprocess.check_output(
        ["git", "show", "--stat", commit_hash]
    ).decode("utf-8")

    return diff[:1500]  # truncate for embedding
