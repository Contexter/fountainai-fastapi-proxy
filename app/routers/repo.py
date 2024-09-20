# app/routers/repo.py
# Router file handling repository-related operations (commits, branches, metadata).

from fastapi import APIRouter, HTTPException, Path
from services.github_service import github_request

router = APIRouter(
    prefix="/repo",
    tags=["repository"],
    responses={404: {"description": "Not found"}}
)

@router.get("/{owner}/{repo}/file/{path:path}/lines", summary="Retrieve file content by line range",
            description="Get a specific range of lines from a large file in the repository.")
def get_lines_by_range(owner: str, repo: str, path: str, start_line: int = 0, end_line: int = None):
    # Placeholder for logic
    pass

@router.get("/{owner}/{repo}", summary="Retrieve repository metadata",
            description="Retrieve metadata about the repository, including stars, forks, watchers, and more.")
def get_repo_info(owner: str = Path(..., description="GitHub username or organization"),
                  repo: str = Path(..., description="Repository name")):
    endpoint = f"repos/{owner}/{repo}"
    return github_request(endpoint)

@router.get("/{owner}/{repo}/commits", summary="Retrieve commit history",
            description="Get a list of commits in the repository.")
def get_commit_history(owner: str = Path(..., description="GitHub username or organization"),
                       repo: str = Path(..., description="Repository name")):
    endpoint = f"repos/{owner}/{repo}/commits"
    return github_request(endpoint)

@router.get("/{owner}/{repo}/branches", summary="List repository branches",
            description="Retrieve a list of branches in the repository.")
def list_branches(owner: str = Path(..., description="GitHub username or organization"),
                  repo: str = Path(..., description="Repository name")):
    endpoint = f"repos/{owner}/{repo}/branches"
    return github_request(endpoint)
