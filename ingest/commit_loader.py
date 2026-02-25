from git import Repo


class CommitLoader:
    def __init__(self, repo_path):
        self.repo = Repo(repo_path)

    def get_commits(self, max_count=50):
        commits_data = []

        for commit in list(self.repo.iter_commits())[:max_count]:
            diffs = commit.diff(commit.parents[0]) if commit.parents else []
            diff_text = ""

            for diff in diffs:
                try:
                    diff_text += diff.diff.decode("utf-8", errors="ignore")
                except:
                    continue

            commits_data.append({
                "commit_id": commit.hexsha,
                "message": commit.message,
                "diff": diff_text
            })

        return commits_data
