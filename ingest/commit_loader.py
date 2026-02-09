import subprocess

def load_commits(since="2024-01-01", max_commits=500):
    cmd = [
        "git", "log",
        f"--since={since}",
        f"-n{max_commits}",
        "--pretty=format:%H||%ad||%s",
        "--date=short"
    ]
    output = subprocess.check_output(cmd).decode("utf-8")
    commits = []

    for line in output.split("\n"):
        h, date, msg = line.split("||")
        commits.append({
            "hash": h,
            "date": date,
            "message": msg
        })
    return commits
