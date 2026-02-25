import os
import shutil
from git import Repo


class RepoLoader:
    def __init__(self, repo_url, local_path="temp_repo"):
        self.repo_url = repo_url
        self.local_path = local_path

    def clone(self):
        if os.path.exists(self.local_path):
            shutil.rmtree(self.local_path)
        Repo.clone_from(self.repo_url, self.local_path)
        return self.local_path
