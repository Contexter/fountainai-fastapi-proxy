import os
from fastapi import FastAPI, HTTPException, Query
import requests
from typing import Optional, List
import logging

# Set up FastAPI app with OpenAPI versioning and custom settings
app = FastAPI(
    title="FountainAI GitHub Repository Proxy API (GraphQL GitHub Issues)",
    version="2.0.0",
    description="This API allows dynamic interaction with GitHub repositories, including file management, commit history, and GitHub Issues using GraphQL for issue management.",
    openapi_version="3.1.0",
    servers=[
        {
            "url": "https://proxy.fountain.coach",
            "description": "Production server for managing GitHub repositories and issues"
        }
    ]
)

# Load the GitHub token from environment variables for security
GITHUB_API_URL = "https://api.github.com"
GITHUB_GRAPHQL_API_URL = "https://api.github.com/graphql"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Now loaded securely from environment variables
if not GITHUB_TOKEN:
    raise HTTPException(status_code=500, detail="GitHub token not found in environment variables")

CHUNK_SIZE = 50000  # 50 KB chunk size for large files
MAX_FILE_SIZE_BYTES = 1024 * 1024  # 1 MB soft limit for comprehensive retrieval

# Set up logging to capture all log levels and write to a log file
logging.basicConfig(
    filename='app.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Helper function to make GraphQL requests to GitHub
def github_graphql_query(query: str, variables: dict = {}):
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.post(GITHUB_GRAPHQL_API_URL, json={"query": query, "variables": variables}, headers=headers)
    if response.status_code != 200:
        logging.error(f"GraphQL API error: {response.status_code}, {response.text}")
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

# Helper function to make REST requests to GitHub API using the token from env variables
def github_request(endpoint: str, method="GET", headers=None, json_data=None):
    url = f"{GITHUB_API_URL}/{endpoint}"
    if headers is None:
        headers = {"Accept": "application/vnd.github.v3+json", "Authorization": f"Bearer {GITHUB_TOKEN}"}
    
    if method == "GET":
        response = requests.get(url, headers=headers)
    elif method == "POST":
        response = requests.post(url, headers=headers, json=json_data)
    elif method == "PATCH":
        response = requests.patch(url, headers=headers, json=json_data)
    elif method == "PUT":
        response = requests.put(url, headers=headers, json=json_data)
    elif method == "DELETE":
        response = requests.delete(url, headers=headers)

    if response.status_code not in [200, 201, 204]:
        logging.error(f"GitHub API error: {response.status_code}, {response.text}")
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response

# ------- ROOT Welcome -------
@app.get("/",
    operation_id="welcomeMessage",
    summary="Welcome to the GitHub Repository Proxy API",
    description="Provides a simple welcome message and confirms that the API is operational."
)
def root():
    return {"message": "Welcome to FountainAI GitHub Repository Proxy API. Manage your repositories and issues dynamically."}

# ------- GraphQL-Based GitHub Issues Operations -------

# Query to list issues with GraphQL
@app.get("/repos/{owner}/{repo}/issues",
    operation_id="listGitHubIssuesGraphQL",
    summary="List GitHub issues using GraphQL",
    description="This endpoint uses GraphQL to retrieve a list of GitHub issues for the specified repository, allowing flexible data retrieval."
)
def list_issues(owner: str, repo: str, first: int = 10, after: Optional[str] = None):
    query = """
    query($owner: String!, $repo: String!, $first: Int!, $after: String) {
      repository(owner: $owner, name: $repo) {
        issues(first: $first, after: $after) {
          edges {
            node {
              title
              body
              state
              createdAt
              author {
                login
              }
            }
            cursor
          }
          pageInfo {
            endCursor
            hasNextPage
          }
        }
      }
    }
    """
    variables = {"owner": owner, "repo": repo, "first": first, "after": after}
    result = github_graphql_query(query, variables)
    
    issues = []
    for edge in result["data"]["repository"]["issues"]["edges"]:
        issues.append({
            "title": edge["node"]["title"],
            "body": edge["node"]["body"],
            "state": edge["node"]["state"],
            "createdAt": edge["node"]["createdAt"],
            "author": edge["node"]["author"]["login"],
            "cursor": edge["cursor"]
        })

    page_info = result["data"]["repository"]["issues"]["pageInfo"]
    
    return {
        "issues": issues,
        "pageInfo": {
            "endCursor": page_info["endCursor"],
            "hasNextPage": page_info["hasNextPage"]
        }
    }

# Query to create an issue with GraphQL
@app.post("/repos/{owner}/{repo}/issues",
    operation_id="createGitHubIssueGraphQL",
    summary="Create a new GitHub issue using GraphQL",
    description="This endpoint uses GraphQL to create a new issue in the specified repository. The title and optional body can be provided."
)
def create_issue(owner: str, repo: str, title: str, body: Optional[str] = None):
    query = """
    mutation($repoId: ID!, $title: String!, $body: String) {
      createIssue(input: {repositoryId: $repoId, title: $title, body: $body}) {
        issue {
          id
          title
          body
          createdAt
        }
      }
    }
    """
    
    # First, we need to fetch the repository ID using GraphQL
    repo_query = """
    query($owner: String!, $repo: String!) {
      repository(owner: $owner, name: $repo) {
        id
      }
    }
    """
    repo_result = github_graphql_query(repo_query, {"owner": owner, "repo": repo})
    repo_id = repo_result["data"]["repository"]["id"]

    variables = {"repoId": repo_id, "title": title, "body": body or ""}
    result = github_graphql_query(query, variables)
    
    return result["data"]["createIssue"]["issue"]

# Query to update an issue with GraphQL
@app.patch("/repos/{owner}/{repo}/issues/{issue_number}",
    operation_id="updateGitHubIssueGraphQL",
    summary="Update a GitHub issue using GraphQL",
    description="This endpoint uses GraphQL to update the title or body of an existing issue in the specified repository."
)
def update_issue(owner: str, repo: str, issue_number: int, title: Optional[str] = None, body: Optional[str] = None):
    query = """
    mutation($issueId: ID!, $title: String!, $body: String!) {
      updateIssue(input: {id: $issueId, title: $title, body: $body}) {
        issue {
          id
          title
          body
        }
      }
    }
    """

    # First, we need to fetch the issue ID using REST API to map the issue number to the issue ID
    issue_data = github_request(f"repos/{owner}/{repo}/issues/{issue_number}")
    issue_id = issue_data["node_id"]

    variables = {"issueId": issue_id, "title": title or issue_data["title"], "body": body or issue_data["body"]}
    result = github_graphql_query(query, variables)
    
    return result["data"]["updateIssue"]["issue"]

# ------- Existing REST-Based File and Commit Operations -------

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

# Fetch file lines by range
@app.get("/repo/{owner}/{repo}/file/{path:path}/lines",
    operation_id="getFileLinesByRange",
    summary="Get file lines by range",
    description="Retrieves a specific range of lines from a file in a GitHub repository. This route is optimized to prevent out-of-range errors by validating the requested line range."
)
def get_lines_by_range(owner: str, repo: str, path: str, start_line: int = 0, end_line: Optional[int] = None):
    logging.info(f"Fetching lines from file: {path} in repo: {repo}")
    try:
        total_lines = count_total_lines(owner, repo, path)

        if start_line < 0 or start_line >= total_lines:
            raise HTTPException(status_code=400, detail=f"Start line is out of range. The file has {total_lines} lines.")

        if end_line is None or end_line > total_lines:
            end_line = total_lines

        total_content = get_file_content(owner, repo, path)["content"]
        lines = total_content.splitlines()
        return {"lines": lines[start_line:end_line], "max_lines": total_lines}

    except requests.exceptions.RequestException as e:
        error_info = {
            "error": str(e),
            "endpoint": f"repos/{owner}/{repo}/contents/{path}",
            "owner": owner,
            "repo": repo,
            "path": path,
            "suggestions": [
                "Check if the line range is valid.",
                "Ensure the file exists in the repository and contains readable content.",
                "If this is a large file, consider chunking your requests for better performance."
            ],
        }
        logging.error(f"Failed to retrieve lines from {path} in {repo}: {error_info}")
        raise HTTPException(status_code=500, detail=error_info)

# Function to calculate total lines in a file
def count_total_lines(owner: str, repo: str, path: str):
    logging.info(f"Counting lines for {path} in {repo}")
    
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
                "Check if the file exists and is accessible.",
                "Ensure that the repository and file path are correct."
            ],
        }
        logging.error(f"Failed to count lines for {path} in {repo}: {error_info}")
        raise HTTPException(status_code=500, detail=error_info)
    
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

# Helper function to process chunk into lines
def process_chunk(chunk, carry_over):
    content = carry_over + chunk
    lines = content.splitlines(keepends=True)
    if not content.endswith("\n"):
        carry_over = lines.pop()
    else:
        carry_over = ""
    return lines, carry_over

# Get the maximum number of lines in the file
@app.get("/repo/{owner}/{repo}/file/{path:path}/max-lines",
    operation_id="getMaxLinesInFile",
    summary="Get maximum line count in file",
    description="Calculates and returns the total number of lines in a file. This is useful for validating line ranges before making a request for specific lines."
)
def get_max_lines(owner: str, repo: str, path: str):
    try:
        total_lines = count_total_lines(owner, repo, path)
        return {"max_lines": total_lines}
    except requests.exceptions.RequestException as e:
        error_info = {
            "error": str(e),
            "endpoint": f"repos/{owner}/{repo}/contents/{path}",
            "owner": owner,
            "repo": repo,
            "path": path,
            "suggestions": [
                "Check if the file exists and is accessible.",
                "Ensure that the repository and file path are correct."
            ],
        }
        logging.error(f"Failed to calculate max lines for {path} in {repo}: {error_info}")
        raise HTTPException(status_code=500, detail=error_info)

# Fetch recent commits for the repository
@app.get("/repo/{owner}/{repo}/commits", summary="Fetch GitHub commit history with pagination support")
def get_commits_by_date(
    owner: str,
    repo: str,
    limit: int = Query(5, description="Number of commits to fetch per page"),
    cursor: Optional[str] = Query(None, description="Cursor for fetching the next page of commits"),
    start_date: Optional[str] = Query(None, description="Filter commits starting from this date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter commits until this date (YYYY-MM-DD)")
):
    """
    Fetch the most recent commits from a GitHub repository, with pagination support and optional date filtering.
    """
    query = """
    query($owner: String!, $repo: String!, $limit: Int!, $cursor: String) {
      repository(owner: $owner, name: $repo) {
        ref(qualifiedName: "main") {
          target {
            ... on Commit {
              history(first: $limit, after: $cursor) {
                edges {
                  cursor
                  node {
                    message
                    committedDate
                  }
                }
                pageInfo {
                  hasNextPage
                  endCursor
                }
              }
            }
          }
        }
      }
    }
    """
    
    variables = {"owner": owner, "repo": repo, "limit": limit, "cursor": cursor}
    result = github_graphql_query(query, variables)
    
    # Filter commits by date if start_date and end_date are provided
    commits = []
    for commit in result["data"]["repository"]["ref"]["target"]["history"]["edges"]:
        commit_date = commit["node"]["committedDate"]
        
        # Only add the commit if it's within the specified date range
        if (not start_date or commit_date >= start_date) and (not end_date or commit_date <= end_date):
            commits.append({
                "message": commit["node"]["message"],
                "cursor": commit["cursor"],
                "committedDate": commit_date
            })
    
    page_info = result["data"]["repository"]["ref"]["target"]["history"]["pageInfo"]
    
    return {
        "commits": commits,
        "pageInfo": {
            "hasNextPage": page_info["hasNextPage"],
            "endCursor": page_info["endCursor"]
        }
    }
