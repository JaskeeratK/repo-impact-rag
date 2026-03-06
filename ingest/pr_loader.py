from github import Github
import os


class PRLoader:
    def __init__(self, repo_name):
        self.client = Github(os.getenv("gh_token"))
        self.repo = self.client.get_repo(repo_name)

    def get_prs(self, limit=20):
        prs = []
        for pr in self.repo.get_pulls(state="all")[:limit]:
            prs.append({
                "title": pr.title,
                "body": pr.body
            })
        return prs
