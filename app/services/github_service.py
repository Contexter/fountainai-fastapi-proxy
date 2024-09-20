import requests

# Service to handle GitHub API interactions
class GitHubService:
    def __init__(self, base_url="https://api.github.com"):
        self.base_url = base_url

    def get_repo_info(self, owner, repo):
        url = f"{self.base_url}/repos/{owner}/{repo}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def list_branches(self, owner, repo):
        url = f"{self.base_url}/repos/{owner}/{repo}/branches"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def get_commit_history(self, owner, repo):
        url = f"{self.base_url}/repos/{owner}/{repo}/commits"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
