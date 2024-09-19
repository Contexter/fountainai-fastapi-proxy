from fastapi import FastAPI, HTTPException, Path
import requests
from typing import Optional

# Define the FastAPI app and set the production server
app = FastAPI(
    title="FountainAI GitHub Repository Controller",
    description="A non-destructive proxy to retrieve metadata, file contents, commit history, pull requests, issues, and traffic insights from the FountainAI GitHub repository.",
    version="1.0.0",
    contact={
        "name": "FountainAI",
        "email": "mail@benedikt-eickhoff.de"
    },
    servers=[
        {
            "url": "https://proxy.fountain.coach",
            "description": "Production server"
        }
    ]
)

GITHUB_API_URL = "https://api.github.com"
CHUNK_SIZE = 50000  # 50 KB chunk size for large files
MAX_FILE_SIZE_BYTES = 1024 * 1024  # 1 MB soft limit for GitHub API

# Helper function to make requests to GitHub API
def github_request(endpoint: str, params=None, headers=None):
    url = f"{GITHUB_API_URL}/{endpoint}"
    if headers is None:
        headers = {
            "Accept": "application/vnd.github.v3+json"
        }
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code not in [200, 206]:
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
    endpoint = f"repos/{owner}/{repo}/contents/{path}" if path else f"repos/{owner}/{repo}/contents"
    return github_request(endpoint)

# 3. Get File Content
@app.get("/repo/{owner}/{repo}/file/{path:path}", operation_id="get_file_content", summary="Retrieve file content",
         description="Get the content of a specific file in the repository. The content is base64-encoded and must be decoded.")
def get_file_content(owner: str = Path(..., description="GitHub username or organization"),
                     repo: str = Path(..., description="Repository name"),
                     path: str = Path(..., description="Path to the file in the repository.")):
    endpoint = f"repos/{owner}/{repo}/contents/{path}"
    file_content = github_request(endpoint)

    # Check file size and raise error if the file is too large
    if file_content.get("size", 0) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="File too large to retrieve in a single request.")
    
    # Decode the base64 content if necessary
    if file_content.get("encoding") == "base64":
        import base64
        file_content["content"] = base64.b64decode(file_content["content"]).decode('utf-8')
    
    return file_content

# Fetch the SHA of a file from the GitHub /contents/ API
def get_file_sha(owner: str, repo: str, path: str):
    """
    Fetch file metadata to retrieve the SHA of the file.
    Internal method not exposed to users.
    """
    endpoint = f"repos/{owner}/{repo}/contents/{path}"
    file_metadata = github_request(endpoint)
    
    # Extract the file's SHA
    file_sha = file_metadata.get("sha")
    
    if not file_sha:
        raise HTTPException(status_code=404, detail="SHA not found for the file.")
    
    return file_sha

# Fetch a chunk of the blob using the GitHub /git/blobs/:sha API
def get_file_in_chunks(owner: str, repo: str, sha: str, start_byte: int, chunk_size: int = CHUNK_SIZE):
    """
    Fetch a large file from GitHub in byte chunks using the blob API.
    Internal method not exposed to users.
    """
    endpoint = f"repos/{owner}/{repo}/git/blobs/{sha}"
    
    # Simulate a byte-range request
    headers = {
        'Range': f'bytes={start_byte}-{start_byte + chunk_size - 1}'  # Fetch chunk of size `chunk_size`
    }
    response = requests.get(endpoint, headers=headers)
    
    if response.status_code != 206:  # Expect Partial Content (206) for range requests
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch blob chunk.")
    
    blob_data = response.json()
    
    # Decode the base64 content (GitHub blobs are base64 encoded)
    if blob_data.get("encoding") == "base64":
        import base64
        decoded_content = base64.b64decode(blob_data["content"]).decode('utf-8')
    else:
        decoded_content = blob_data["content"]
    
    return decoded_content

# Process the chunk of content and split into lines, handling any incomplete lines
def process_chunk(chunk: str, carry_over: str = ""):
    """
    Process a chunk of text, split it into lines, and handle incomplete lines by carrying them over.
    Internal method.
    """
    lines = (carry_over + chunk).splitlines(True)  # Preserve line breaks
    if not lines:
        return [], ""

    # If the last line doesn't end with a newline, it's incomplete; carry it over
    if not lines[-1].endswith(('\n', '\r\n')):
        carry_over = lines.pop()  # Carry over the last incomplete line
    else:
        carry_over = ""
    
    return lines, carry_over

# Public API to retrieve specific lines from a large file
@app.get("/repo/{owner}/{repo}/file/{path:path}/lines", operation_id="get_file_lines", summary="Retrieve file content by line range",
         description="Get a specific range of lines from a large file in the repository.")
def get_lines_by_range(owner: str, repo: str, path: str, start_line: int = 0, end_line: Optional[int] = None):
    """
    Public-facing method to retrieve specific lines from a large file by reading it in chunks.
    """
    # Initialization
    start_byte = 0
    total_lines = []
    carry_over = ""

    # Step 1: Fetch the file SHA (internal process)
    file_sha = get_file_sha(owner, repo, path)
    
    # Step 2: Fetch and process chunks until we have the requested lines
    while len(total_lines) < (end_line or start_line + 100):  # Fetch until we have enough lines
        chunk = get_file_in_chunks(owner, repo, file_sha, start_byte, CHUNK_SIZE)
        
        # Process the chunk into lines
        lines, carry_over = process_chunk(chunk, carry_over)
        total_lines.extend(lines)
        
        # Update byte pointer for the next chunk
        start_byte += CHUNK_SIZE

    # Step 3: Return the requested lines
    return {"lines": total_lines[start_line:end_line]}

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
