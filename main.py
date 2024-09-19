from fastapi import FastAPI, HTTPException, Path
import requests
from typing import Optional
import logging
import os
from datetime import datetime

# Set up verbose logging to capture all log levels and write to a log file
logging.basicConfig(
    filename='app.log',
    level=logging.DEBUG,   # Capture DEBUG level logs for full verbosity
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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
    logging.info(f"Making GitHub API request to: {url}")
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code not in [200, 206]:
        logging.error(f"GitHub API error: {response.status_code}, {response.text}")
        raise HTTPException(status_code=response.status_code, detail=response.json())
    
    return response.json()

# Route to retrieve specific lines from a large file
@app.get("/repo/{owner}/{repo}/file/{path:path}/lines", operation_id="get_file_lines", summary="Retrieve file content by line range",
         description="Get a specific range of lines from a large file in the repository.")
def get_lines_by_range(owner: str, repo: str, path: str, start_line: int = 0, end_line: Optional[int] = None):
    logging.info(f"Fetching lines from file: {path} in repo: {repo}")

    if start_line < 0 or (end_line is not None and end_line < start_line):
        raise HTTPException(status_code=400, detail="Invalid line range.")

    # Variables for tracking progress
    start_byte = 0
    total_lines = []
    carry_over = ""

    # Fetch the file's SHA (GitHub-specific, assuming this is needed)
    try:
        file_sha = get_file_sha(owner, repo, path)
    except Exception as e:
        logging.error(f"Error fetching SHA for file {path}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching SHA: {str(e)}")

    # Process chunks until we gather all requested lines
    while len(total_lines) < (end_line or start_line + 100):
        try:
            # Fetch file in chunks
            chunk = get_file_in_chunks(owner, repo, file_sha, start_byte, CHUNK_SIZE)  # Fetch chunk
        except Exception as e:
            logging.error(f"Error fetching file chunk for {path}: {e}")
            raise HTTPException(status_code=500, detail=f"Error fetching file chunk: {str(e)}")

        # Process the chunk into lines
        lines, carry_over = process_chunk(chunk, carry_over)
        total_lines.extend(lines)

        # Update byte pointer for the next chunk
        start_byte += CHUNK_SIZE

    logging.info(f"Successfully fetched lines from {path}")
    
    # Return the requested lines
    return {"lines": total_lines[start_line:end_line]}

# Fetch file content in chunks by byte-range
def get_file_in_chunks(owner, repo, sha, start_byte, chunk_size):
    url = f"https://api.github.com/repos/{owner}/{repo}/git/blobs/{sha}"
    headers = {
        "Accept": "application/vnd.github.v3.raw",
        "Range": f"bytes={start_byte}-{start_byte + chunk_size - 1}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200 and "Range" not in response.headers:
        logging.info("File is small enough to retrieve without chunking.")
        return response.content
    elif response.status_code != 206:  # Expecting Partial Content for chunked files
        logging.error(f"Failed to fetch chunk from file, status code: {response.status_code}")
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch file chunk.")
    return response.content

# Process a chunk into lines, handling incomplete lines
def process_chunk(chunk, carry_over):
    # Combine the chunk with any remaining content from the previous chunk
    content = carry_over + chunk.decode("utf-8")
    
    # Split the content into lines
    lines = content.splitlines(keepends=True)  # Keep end-of-line characters
    
    # Handle the case where the last line may be incomplete
    if not content.endswith("\n"):
        carry_over = lines.pop()  # Store the incomplete last line for the next chunk
    else:
        carry_over = ""
    
    return lines, carry_over

# Get file SHA using GitHub API
def get_file_sha(owner, repo, path):
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    response = requests.get(url)
    if response.status_code != 200:
        logging.error(f"Failed to retrieve file SHA for {path}")
        raise HTTPException(status_code=response.status_code, detail="Failed to retrieve file SHA.")
    return response.json().get("sha")

# Route to retrieve repository information
@app.get("/repo/{owner}/{repo}", operation_id="get_repo_info", summary="Retrieve repository metadata",
         description="Retrieve metadata about the repository, including stars, forks, watchers, open issues, default branch, visibility (public/private), and description.")
def get_repo_info(owner: str = Path(..., description="GitHub username or organization"),
                  repo: str = Path(..., description="Repository name")):
    endpoint = f"repos/{owner}/{repo}"
    return github_request(endpoint)

# Route to list repository contents
@app.get("/repo/{owner}/{repo}/contents", operation_id="list_repo_contents", summary="List repository contents",
         description="List the files and directories in the repository, including file names, file size, type (file or directory), and download URLs.")
def list_repo_contents(owner: str = Path(..., description="GitHub username or organization"),
                       repo: str = Path(..., description="Repository name"),
                       path: Optional[str] = None):
    endpoint = f"repos/{owner}/{repo}/contents/{path}" if path else f"repos/{owner}/{repo}/contents"
    return github_request(endpoint)

# Route to commit and push logs to GitHub
def commit_and_push_logs():
    try:
        # Get the current working directory (assumed to be the repo path)
        repo_path = os.getcwd()

        # Check if the current directory is a Git repository
        if not os.path.exists(os.path.join(repo_path, '.git')):
            raise Exception("Current directory is not a Git repository.")

        # Commit message with timestamp
        commit_message = f"Log update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        # Stage the log file, commit, and push
        os.system('git add app.log')  # Stage the log file
        os.system(f'git commit -m "{commit_message}"')  # Commit with a message
        os.system('git push origin main')  # Push to the main branch

        return "Logs have been successfully committed and pushed to GitHub."

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error committing logs: {str(e)}")

# Route to trigger log push
@app.get("/push-logs", summary="Push logs to GitHub", description="Triggers a log commit and pushes it to GitHub.")
async def push_logs():
    try:
        message = commit_and_push_logs()
        return {"message": message}
    except HTTPException as e:
        return {"error": e.detail}

# Route to retrieve commit history
@app.get("/repo/{owner}/{repo}/commits", operation_id="get_commit_history", summary="Retrieve commit history",
         description="Get a list of commits in the repository, including the author, commit message, timestamp, and files changed in each commit.")
def get_commit_history(owner: str = Path(..., description="GitHub username or organization"),
                       repo: str = Path(..., description="Repository name")):
    endpoint = f"repos/{owner}/{repo}/commits"
    return github_request(endpoint)

# Route to retrieve pull requests
@app.get("/repo/{owner}/{repo}/pulls", operation_id="list_pull_requests", summary="List pull requests",
         description="Retrieve a list of pull requests for the repository, including title, status (open, closed, merged), author, and review status.")
def list_pull_requests(owner: str = Path(..., description="GitHub username or organization"),
                       repo: str = Path(..., description="Repository name")):
    endpoint = f"repos/{owner}/{repo}/pulls"
    return github_request(endpoint)

# Route to retrieve issues
@app.get("/repo/{owner}/{repo}/issues", operation_id="list_issues", summary="List issues",
         description="Retrieve a list of issues for the repository, including title, status (open or closed), author, and assigned labels.")
def list_issues(owner: str = Path(..., description="GitHub username or organization"),
                repo: str = Path(..., description="Repository name")):
    endpoint = f"repos/{owner}/{repo}/issues"
    return github_request(endpoint)

# Route to retrieve repository branches
@app.get("/repo/{owner}/{repo}/branches", operation_id="list_branches", summary="List repository branches",
         description="Retrieve a list of branches in the repository, including branch name and whether the branch is protected.")
def list_branches(owner: str = Path(..., description="GitHub username or organization"),
                  repo: str = Path(..., description="Repository name")):
    endpoint = f"repos/{owner}/{repo}/branches"
    return github_request(endpoint)

# Route to retrieve traffic views
@app.get("/repo/{owner}/{repo}/traffic/views", operation_id="get_traffic_views", summary="Retrieve repository traffic views",
         description="Get the number of views for the repository over a specified time period.")
def get_repo_traffic_views(owner: str = Path(..., description="GitHub username or organization"),
                           repo: str = Path(..., description="Repository name")):
    endpoint = f"repos/{owner}/{repo}/traffic/views"
    return github_request(endpoint)

# Route to retrieve traffic clones
@app.get("/repo/{owner}/{repo}/traffic/clones", operation_id="get_traffic_clones", summary="Retrieve repository traffic clones",
         description="Get the number of times the repository has been cloned over a specified time period.")
def get_repo_traffic_clones(owner: str = Path(..., description="GitHub username or organization"),
                            repo: str = Path(..., description="Repository name")):
    endpoint = f"repos/{owner}/{repo}/traffic/clones"
    return github_request(endpoint)
