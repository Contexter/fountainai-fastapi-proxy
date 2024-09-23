from fastapi import FastAPI, HTTPException, Path
import requests
from typing import Optional
import logging

app = FastAPI(
    title="FountainAI GitHub Repository File Content API",
    version="1.1.0",
    description="This API enables efficient retrieval and management of file content from GitHub repositories. It returns file paths in the same format as GitHub's 'Copy file path' feature.",
    openapi_version="3.1.0"
)

GITHUB_API_URL = "https://api.github.com"
CHUNK_SIZE = 50000  # 50 KB chunk size for large files
MAX_FILE_SIZE_BYTES = 1024 * 1024  # 1 MB soft limit for comprehensive retrieval

# Set up logging to capture all log levels and write to a log file
logging.basicConfig(
    filename='app.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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

# Fetch the repository directory structure (recursive tree)
@app.get("/repo/{owner}/{repo}/tree",
    operation_id="getRepositoryTree",
    summary="Retrieve repository directory structure with 'Copy file path' format",
    description="Fetches the recursive directory structure of a GitHub repository. Returns file paths in the same format as GitHub's 'Copy file path' feature."
)
def get_repo_tree(owner: str, repo: str):
    logging.info(f"Fetching repository tree for {repo} by {owner}")
    try:
        endpoint = f"repos/{owner}/{repo}/git/trees/main?recursive=1"
        tree_data = github_request(endpoint)
        # Extract the relevant part of the tree to return in "Copy file path" format
        paths = []
        for item in tree_data.json().get("tree", []):
            if item["type"] == "blob":  # Only include files, not directories
                paths.append(item["path"])  # 'path' is in "Copy file path" format
        return {"file_paths": paths}
    except requests.exceptions.RequestException as e:
        error_info = {
            "error": str(e),
            "endpoint": endpoint,
            "owner": owner,
            "repo": repo,
            "suggestions": [
                "Check if the repository is public or accessible with proper permissions.",
                "Ensure the repository name and owner are correct.",
                "Check if the repository has a 'main' branch or if it's using a different default branch.",
                "Consider if GitHub API rate limits or access restrictions are being applied."
            ],
        }
        logging.error(f"Repository tree retrieval failed for {repo} by {owner}: {error_info}")
        raise HTTPException(status_code=500, detail=error_info)

# Fetch file content by its path, chunked if necessary
@app.get("/repo/{owner}/{repo}/file/{path:path}/content",
    operation_id="getFileContent",
    summary="Get file content from repository using 'Copy file path' format",
    description="Retrieves the content of a file from a GitHub repository using the path format from GitHub's 'Copy file path' feature. For smaller files, the entire content is returned in one response."
)
def get_file_content(owner: str, repo: str, path: str):
    logging.info(f"Fetching file content for {path} in {repo} by {owner}")
    try:
        metadata = github_request(f"repos/{owner}/{repo}/contents/{path}")
        file_data = metadata.json()
        file_size = file_data.get("size", 0)
        sha = file_data.get("sha")
    except requests.exceptions.RequestException as e:
        error_info = {
            "error": str(e),
            "endpoint": f"repos/{owner}/{repo}/contents/{path}",
            "owner": owner,
            "repo": repo,
            "path": path,
            "suggestions": [
                "Ensure the file path exists within the repository (in 'Copy file path' format).",
                "Check if the file is accessible and not too large for API retrieval.",
                "Verify that the repository is public or your API token has sufficient access."
            ],
        }
        logging.error(f"Failed to retrieve file content for {path} in {repo}: {error_info}")
        raise HTTPException(status_code=500, detail=error_info)

    total_content = ""
    start_byte = 0

    while start_byte < file_size:
        chunk = get_file_chunk(owner, repo, sha, start_byte, CHUNK_SIZE)
        total_content += chunk
        start_byte += CHUNK_SIZE

    return {"content": total_content}

# Helper function to retrieve file chunk by byte range
def get_file_chunk(owner: str, repo: str, sha: str, start_byte: int, chunk_size: int):
    url = f"https://api.github.com/repos/{owner}/{repo}/git/blobs/{sha}"
    headers = {"Accept": "application/vnd.github.v3.raw", "Range": f"bytes={start_byte}-{start_byte + chunk_size - 1}"}
    response = requests.get(url, headers=headers)
    if response.status_code != 206 and response.status_code != 200:
        raise HTTPException(status_code=500, detail="Error fetching file chunk.")
    return response.content.decode("utf-8")

# Rest of the functions remain the same...
