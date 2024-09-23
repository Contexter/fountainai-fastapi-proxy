from fastapi import FastAPI, HTTPException, Path
import requests
from typing import Optional
import logging
import os
from datetime import datetime

# Set up logging to capture all log levels and write to a log file
logging.basicConfig(
    filename='app.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Initialize the FastAPI app and define production server settings
app = FastAPI(
    title="FountainAI GitHub Repository Controller",
    description="A proxy API for retrieving metadata, file contents, commit history, pull requests, issues, and traffic insights from a GitHub repository. It also handles file chunking for large files.",
    version="1.1.0",
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
MAX_FILE_SIZE_BYTES = 1024 * 1024  # 1 MB soft limit for comprehensive retrieval

# Helper function to make requests to GitHub API
def github_request(endpoint: str, headers=None):
    url = f"{GITHUB_API_URL}/{endpoint}"
    if headers is None:
        headers = {"Accept": "application/vnd.github.v3+json"}
    response = requests.get(url, headers=headers)
    if response.status_code not in [200, 206]:
        logging.error(f"GitHub API error: {response.status_code}, {response.text}")
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response

# Helper function to fetch file content in chunks
def get_file_chunk(owner: str, repo: str, sha: str, start_byte: int, chunk_size: int):
    url = f"https://api.github.com/repos/{owner}/{repo}/git/blobs/{sha}"
    headers = {"Accept": "application/vnd.github.v3.raw", "Range": f"bytes={start_byte}-{start_byte + chunk_size - 1}"}
    response = requests.get(url, headers=headers)
    if response.status_code != 206 and response.status_code != 200:
        raise HTTPException(status_code=500, detail="Error fetching file chunk.")
    return response.content.decode("utf-8")

# Function to calculate the total number of lines in a file
def count_total_lines(owner: str, repo: str, path: str):
    logging.info(f"Counting lines for {path} in {repo}")
    
    try:
        metadata = github_request(f"repos/{owner}/{repo}/contents/{path}")
        file_data = metadata.json()
        file_size = file_data.get("size", 0)
        sha = file_data.get("sha")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching file metadata: {str(e)}")
    
    total_lines = 0
    carry_over = ""
    start_byte = 0
    
    while start_byte < file_size:
        chunk = get_file_chunk(owner, repo, sha, start_byte, CHUNK_SIZE)
        lines, carry_over = process_chunk(chunk, carry_over)
        total_lines += len(lines)
        start_byte += CHUNK_SIZE

    logging.info(f"Total number of lines in {path}: {total_lines}")
    return total_lines

# Helper function to process a chunk of content into lines
def process_chunk(chunk, carry_over):
    content = carry_over + chunk
    lines = content.splitlines(keepends=True)  # Keep end-of-line characters
    if not content.endswith("\n"):
        carry_over = lines.pop()  # Store incomplete last line for the next chunk
    else:
        carry_over = ""
    return lines, carry_over

# Retrieve file content in chunks or entirely, based on file size
@app.get("/repo/{owner}/{repo}/file/{path:path}/content", summary="Get comprehensive file content")
def get_comprehensive_file_content(owner: str, repo: str, path: str):
    logging.info(f"Retrieving comprehensive file content for {path} in {repo}")
    
    try:
        metadata = github_request(f"repos/{owner}/{repo}/contents/{path}")
        file_data = metadata.json()
        file_size = file_data.get("size", 0)
        sha = file_data.get("sha")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching file metadata: {str(e)}")
    
    total_content = ""
    start_byte = 0
    
    while start_byte < file_size:
        chunk = get_file_chunk(owner, repo, sha, start_byte, CHUNK_SIZE)
        total_content += chunk
        start_byte += CHUNK_SIZE
    
    return total_content

# Function to retrieve file lines by a specified range, returning max lines for debugging
@app.get("/repo/{owner}/{repo}/file/{path:path}/lines", summary="Fetch file content by line range")
def get_lines_by_range(owner: str, repo: str, path: str, start_line: int = 0, end_line: Optional[int] = None):
    logging.info(f"Fetching lines from file: {path} in repo: {repo}")
    
    total_lines = count_total_lines(owner, repo, path)
    
    if start_line < 0 or start_line >= total_lines:
        raise HTTPException(status_code=400, detail=f"Start line is out of range. The file has {total_lines} lines.")
    if end_line is None or end_line > total_lines:
        end_line = total_lines
    
    try:
        total_content = get_comprehensive_file_content(owner, repo, path)
        lines = total_content.splitlines()
        return {"lines": lines[start_line:end_line], "max_lines": total_lines}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching lines: {str(e)}")

# New route to return only the maximum number of lines in a file
@app.get("/repo/{owner}/{repo}/file/{path:path}/max-lines", summary="Get maximum line count in file")
def get_max_lines(owner: str, repo: str, path: str):
    try:
        total_lines = count_total_lines(owner, repo, path)
        return {"max_lines": total_lines}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating total lines: {str(e)}")

# Fetch repository metadata
@app.get("/repo/{owner}/{repo}", summary="Retrieve repository metadata")
def get_repo_info(owner: str = Path(..., description="GitHub username or organization"),
                  repo: str = Path(..., description="Repository name")):
    endpoint = f"repos/{owner}/{repo}"
    return github_request(endpoint)

# List contents of the repository
@app.get("/repo/{owner}/{repo}/contents", summary="List repository contents")
def list_repo_contents(owner: str = Path(..., description="GitHub username or organization"),
                       repo: str = Path(..., description="Repository name"),
                       path: Optional[str] = None):
    endpoint = f"repos/{owner}/{repo}/contents/{path}" if path else f"repos/{owner}/{repo}/contents"
    return github_request(endpoint)

# Push log updates to GitHub
def commit_and_push_logs():
    try:
        repo_path = os.getcwd()
        if not os.path.exists(os.path.join(repo_path, '.git')):
            raise Exception("Current directory is not a Git repository.")
        
        commit_message = f"Log update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        os.system('git add app.log')
        os.system(f'git commit -m \"{commit_message}\"')
        os.system('git push origin main')
        
        return "Logs have been successfully committed and pushed to GitHub."
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error committing logs: {str(e)}")

@app.get("/push-logs", summary="Push logs to GitHub", description="Triggers a log commit and pushes it to GitHub.")
async def push_logs():
    try:
        message = commit_and_push_logs()
        return {"message": message}
    except HTTPException as e:
        return {"error": e.detail}

# Retrieve commit history of the repository
@app.get("/repo/{owner}/{repo}/commits", summary="Retrieve commit history")
def get_commit_history(owner: str = Path(..., description="GitHub username or organization"),
                       repo: str = Path(..., description="Repository name")):
    endpoint = f"repos/{owner}/{repo}/commits"
    return github_request(endpoint)

# Retrieve pull requests for the repository
@app.get("/repo/{owner}/{repo}/pulls", summary="List pull requests")
def list_pull_requests(owner: str = Path(..., description="GitHub username or organization"),
                       repo: str = Path(..., description="Repository name")):
    endpoint = f"repos/{owner}/{repo}/pulls"
    return github_request(endpoint)

# Retrieve issues for the repository
@app.get("/repo/{owner}/{repo}/issues", summary="List issues")
def list_issues(owner: str = Path(..., description="GitHub username or organization"),
                repo: str = Path(..., description="Repository name")):
    endpoint = f"repos/{owner}/{repo}/issues"
    return github_request(endpoint)

# List branches in the repository
@app.get("/repo/{owner}/{repo}/branches", summary="List repository branches")
def list_branches(owner: str = Path(..., description="GitHub username or organization"),
                  repo: str = Path(..., description="Repository name")):
    endpoint = f"repos/{owner}/{repo}/branches"
    return github_request(endpoint)

# Retrieve repository traffic views
@app.get("/repo/{owner}/{repo}/traffic/views", summary="Retrieve repository traffic views")
def get_repo_traffic_views(owner: str = Path(..., description="GitHub username or organization"),
                           repo: str = Path(..., description="Repository name")):
    endpoint = f"repos/{owner}/{repo}/traffic/views"
    return github_request(endpoint)

# Retrieve repository traffic clones
@app.get("/repo/{owner}/{repo}/traffic/clones", summary="Retrieve repository traffic clones")
def get_repo_traffic_clones(owner: str = Path(..., description="GitHub username or organization"),
                            repo: str = Path(..., description="Repository name")):
    endpoint = f"repos/{owner}/{repo}/traffic/clones"
    return github_request(endpoint)
