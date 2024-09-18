import base64
from fastapi import FastAPI, HTTPException, Path
import requests
from typing import Optional

app = FastAPI(
    title="FountainAI GitHub Repository Controller",
    description="A non-destructive proxy to retrieve metadata, file contents, commit history, pull requests, issues, and traffic insights from the FountainAI GitHub repository.",
    version="1.0.0",
    contact={
        "name": "FountainAI Development Team",
        "email": "support@fountainai.dev"
    }
)

GITHUB_API_URL = "https://api.github.com"

# Helper function to make requests to GitHub API
def github_request(endpoint: str, params=None):
    url = f"{GITHUB_API_URL}/{endpoint}"
    headers = {
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    
    return response.json()

# Helper function to decode base64 content
def decode_base64(content):
    decoded_bytes = base64.b64decode(content)
    return decoded_bytes.decode('utf-8')

# 1. Get Repository Information
@app.get("/repo/{owner}/{repo}", operation_id="get_repo_info", summary="Retrieve repository metadata",
         description="Retrieve metadata about the repository, including stars, forks, watchers, open issues, default branch, visibility (public/private), and description.")
def get_repo_info(owner: str = Path(..., description="GitHub username or organization"),
                  repo: str = Path(..., description="Repository name")):
    """
    Retrieve repository metadata such as stars, forks, watchers, open issues, default branch, visibility, and description.
    """
    endpoint = f"repos/{owner}/{repo}"
    return github_request(endpoint)

# 2. List Repository Contents
@app.get("/repo/{owner}/{repo}/contents", operation_id="list_repo_contents", summary="List repository contents",
         description="List the files and directories in the repository, including file names, file size, type (file or directory), and download URLs.")
def list_repo_contents(owner: str = Path(..., description="GitHub username or organization"),
                       repo: str = Path(..., description="Repository name"),
                       path: Optional[str] = Path(None, description="Optional path to a specific directory or file.")):
    """
    List the contents of a repository, such as file names, file sizes, and download URLs for files. You can optionally specify a path to retrieve contents of a specific directory or file.
    """
    endpoint = f"repos/{owner}/{repo}/contents/{path if path else ''}"
    return github_request(endpoint)

# 3. Get File Content (with base64 decoding)
@app.get("/repo/{owner}/{repo}/file/{path:path}", operation_id="get_file_content", summary="Retrieve and decode file content",
         description="Get the content of a specific file in the repository. The content is base64-encoded and decoded to return the file content.")
def get_file_content(owner: str = Path(..., description="GitHub username or organization"),
                     repo: str = Path(..., description="Repository name"),
                     path: str = Path(..., description="Path to the file in the repository.")):
    """
    Retrieve and decode the content of a specific file in the repository.
    """
    endpoint = f"repos/{owner}/{repo}/contents/{path}"
    file_data = github_request(endpoint)
    
    if 'content' in file_data and file_data.get('encoding') == 'base64':
        decoded_content = decode_base64(file_data['content'])
        return {"decoded_content": decoded_content}
    else:
        raise HTTPException(status_code=404, detail="File content not found or not base64-encoded")

# 4. Get Commit History
@app.get("/repo/{owner}/{repo}/commits", operation_id="get_commit_history", summary="Retrieve commit history",
         description="Get a list of commits in the repository, including the author, commit message, timestamp, and files changed in each commit.")
def get_commit_history(owner: str = Path(..., description="GitHub username or organization"),
                       repo: str = Path(..., description="Repository name")):
    """
    Retrieve the commit history of a repository, including the author, commit message, timestamp, and files changed in each commit.
    """
    endpoint = f"repos/{owner}/{repo}/commits"
    return github_request(endpoint)

# 5. List Pull Requests
@app.get("/repo/{owner}/{repo}/pulls", operation_id="list_pull_requests", summary="List pull requests",
         description="Retrieve a list of pull requests for the repository, including title, status (open, closed, merged), author, and review status.")
def list_pull_requests(owner: str = Path(..., description="GitHub username or organization"),
                       repo: str = Path(..., description="Repository name")):
    """
    List all pull requests for a repository, including the title, status (open, closed, or merged), author, and review status.
    """
    endpoint = f"repos/{owner}/{repo}/pulls"
    return github_request(endpoint)

# 6. List Issues
@app.get("/repo/{owner}/{repo}/issues", operation_id="list_issues", summary="List issues",
         description="Retrieve a list of issues for the repository, including title, status (open or closed), author, and assigned labels.")
def list_issues(owner: str = Path(..., description="GitHub username or organization"),
                repo: str = Path(..., description="Repository name")):
    """
    List all issues for a repository, including the title, status (open or closed), author, and assigned labels.
    """
    endpoint = f"repos/{owner}/{repo}/issues"
    return github_request(endpoint)

# 7. List Branches
@app.get("/repo/{owner}/{repo}/branches", operation_id="list_branches", summary="List repository branches",
         description="Retrieve a list of branches in the repository, including branch name and whether the branch is protected.")
def list_branches(owner: str = Path(..., description="GitHub username or organization"),
                  repo: str = Path(..., description="Repository name")):
    """
    List all branches in the repository, including the branch name and whether the branch is protected (i.e., cannot be directly modified).
    """
    endpoint = f"repos/{owner}/{repo}/branches"
    return github_request(endpoint)

# 8. Get Traffic Insights (Views and Clones)
@app.get("/repo/{owner}/{repo}/traffic/views", operation_id="get_traffic_views", summary="Retrieve repository traffic views",
         description="Get the number of views for the repository over a specified time period.")
def get_repo_traffic_views(owner: str = Path(..., description="GitHub username or organization"),
                           repo: str = Path(..., description="Repository name")):
    """
    Retrieve the number of views the repository has received over a specific time period, providing insights into repository visibility and popularity.
    """
    endpoint = f"repos/{owner}/{repo}/traffic/views"
    return github_request(endpoint)

@app.get("/repo/{owner}/{repo}/traffic/clones", operation_id="get_traffic_clones", summary="Retrieve repository traffic clones",
         description="Get the number of times the repository has been cloned over a specified time period.")
def get_repo_traffic_clones(owner: str = Path(..., description="GitHub username or organization"),
                            repo: str = Path(..., description="Repository name")):
    """
    Retrieve the number of times the repository has been cloned over a specific time period, providing insights into how often the repository is replicated.
    """
    endpoint = f"repos/{owner}/{repo}/traffic/clones"
    return github_request(endpoint)

# Run the Uvicorn server (use this command if running from command line)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
