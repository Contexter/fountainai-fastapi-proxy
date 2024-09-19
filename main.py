from fastapi import FastAPI, HTTPException, Path
import requests
from typing import Optional
from fastapi.openapi.models import Server

# Define the FastAPI app and set the production server
app = FastAPI(
    title="FountainAI GitHub Repository Controller",
    description="A non-destructive proxy to retrieve metadata, file contents, commit history, pull requests, issues, and traffic insights from the FountainAI GitHub repository.",
    version="1.0.0",
    contact={
        "name": "FountainAI ",
        "email": "mail@benedikt-eickhoff.de"
    },
    servers=[
        {
            "url": "https://proxy.fountain.coach",
            "description": "Production server"
        }
    ]  # Only the production server
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

# Root route
@app.get("/", summary="Root Endpoint", description="Welcome to the FountainAI GitHub Proxy")
async def read_root():
    return {"message": "Welcome to the FountainAI GitHub Proxy"}

# 1. Get Repository Information
@app.get("/repo/{owner}/{repo}", operation_id="get_repo_info", summary="Retrieve repository metadata",
         description="Retrieve metadata about the repository, including stars, forks, watchers, open issues, default branch, visibility (public/private), and description.")
def get_repo_info(owner: str = Path(..., description="GitHub username or organization"),
                  repo: str = Path(..., description="Repository name")):
    endpoint = f"repos/{owner}/{repo}"
    return github_request(endpoint)

# 2. List Repository Contents
@app.get("/repo/{owner}/{repo}/contents", operation_id="list_repo_contents", summary="List repository contents",
         description="List the files and directories in the repository, including file names, file size, type (file or directory), and download URLs.")
def list_repo_contents(owner: str = Path(..., description="GitHub username or organization"),
                       repo: str = Path(..., description="Repository name"),
                       path: Optional[str] = None):
    """
    Lists contents of the repository. The path parameter is optional.
    """
    if path:
        endpoint = f"repos/{owner}/{repo}/contents/{path}"
    else:
        endpoint = f"repos/{owner}/{repo}/contents"
    
    return github_request(endpoint)

# 3. Get File Content
@app.get("/repo/{owner}/{repo}/file/{path:path}", operation_id="get_file_content", summary="Retrieve file content",
         description="Get the content of a specific file in the repository. The content is base64-encoded and must be decoded.")
def get_file_content(owner: str = Path(..., description="GitHub username or organization"),
                     repo: str = Path(..., description="Repository name"),
                     path: str = Path(..., description="Path to the file in the repository.")):
    endpoint = f"repos/{owner}/{repo}/contents/{path}"
    file_content = github_request(endpoint)
    if file_content.get("encoding") == "base64":
        import base64
        file_content["content"] = base64.b64decode(file_content["content"]).decode('utf-8')
    return file_content

# 4. Get Commit History
@app.get("/repo/{owner}/{repo}/commits", operation_id="get_commit_history", summary="Retrieve commit history",
         description="Get a list of commits in the repository, including the author, commit message, timestamp, and files changed in each commit.")
def get_commit_history(owner: str = Path(..., description="GitHub username or organization"),
                       repo: str = Path(..., description="Repository name")):
    endpoint = f"repos/{owner}/{repo}/commits"
    return github_request(endpoint)

# 5. List Pull Requests
@app.get("/repo/{owner}/{repo}/pulls", operation_id="list_pull_requests", summary="List pull requests",
         description="Retrieve a list of pull requests for the repository, including title, status (open, closed, merged), author, and review status.")
def list_pull_requests(owner: str = Path(..., description="GitHub username or organization"),
                       repo: str = Path(..., description="Repository name")):
    endpoint = f"repos/{owner}/{repo}/pulls"
    return github_request(endpoint)

# 6. List Issues
@app.get("/repo/{owner}/{repo}/issues", operation_id="list_issues", summary="List issues",
         description="Retrieve a list of issues for the repository, including title, status (open or closed), author, and assigned labels.")
def list_issues(owner: str = Path(..., description="GitHub username or organization"),
                repo: str = Path(..., description="Repository name")):
    endpoint = f"repos/{owner}/{repo}/issues"
    return github_request(endpoint)

# 7. List Branches
@app.get("/repo/{owner}/{repo}/branches", operation_id="list_branches", summary="List repository branches",
         description="Retrieve a list of branches in the repository, including branch name and whether the branch is protected.")
def list_branches(owner: str = Path(..., description="GitHub username or organization"),
                  repo: str = Path(..., description="Repository name")):
    endpoint = f"repos/{owner}/{repo}/branches"
    return github_request(endpoint)

# 8. Get Traffic Insights (Views and Clones)
@app.get("/repo/{owner}/{repo}/traffic/views", operation_id="get_traffic_views", summary="Retrieve repository traffic views",
         description="Get the number of views for the repository over a specified time period.")
def get_repo_traffic_views(owner: str = Path(..., description="GitHub username or organization"),
                           repo: str = Path(..., description="Repository name")):
    endpoint = f"repos/{owner}/{repo}/traffic/views"
    return github_request(endpoint)

@app.get("/repo/{owner}/{repo}/traffic/clones", operation_id="get_traffic_clones", summary="Retrieve repository traffic clones",
         description="Get the number of times the repository has been cloned over a specified time period.")
def get_repo_traffic_clones(owner: str = Path(..., description="GitHub username or organization"),
                            repo: str = Path(..., description="Repository name")):
    endpoint = f"repos/{owner}/{repo}/traffic/clones"
    return github_request(endpoint)


# NEW FEATURE: Fetch file content by line range
@app.get("/repo/{owner}/{repo}/file/{path:path}/lines", operation_id="get_file_lines", summary="Retrieve file content by line range",
         description="Get a specific range of lines from a file in the repository.")
def get_file_lines(owner: str = Path(..., description="GitHub username or organization"),
                   repo: str = Path(..., description="Repository name"),
                   path: str = Path(..., description="Path to the file in the repository."),
                   start_line: Optional[int] = 0,
                   end_line: Optional[int] = None):
    """
    Retrieve file content and return a specific range of lines.
    """
    # Fetch the file content using the existing logic
    endpoint = f"repos/{owner}/{repo}/contents/{path}"
    file_content = github_request(endpoint)
    
    # Decode the base64 content if necessary
    if file_content.get("encoding") == "base64":
        import base64
        file_content["content"] = base64.b64decode(file_content["content"]).decode('utf-8')
    
    # Split the content into lines
    lines = file_content["content"].splitlines()
    
    # Set end_line to the total number of lines if not provided
    if end_line is None:
        end_line = len(lines)
    
    # Validate line range
    if start_line < 0 or end_line > len(lines):
        raise HTTPException(status_code=400, detail="Invalid line range")
    
    # Return the requested range of lines
    return {"lines": lines[start_line:end_line]}

