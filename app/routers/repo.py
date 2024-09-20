from fastapi import APIRouter
from app.services.github_service import (
    get_file_lines,
    get_repo_info,
    list_repo_contents,
    get_commit_history,
    list_pull_requests,
    list_issues,
    list_branches,
)

router = APIRouter(
    prefix="/repo",
    tags=["Repository"],
    responses={404: {"description": "Not found"}},
)

@router.get("/{owner}/{repo}/file/{path:path}/lines", summary="Retrieve file lines from repo")
async def get_file(owner: str, repo: str, path: str):
    """
    Retrieve specific lines from a file within a repository.
    
    - **owner**: The repository owner.
    - **repo**: The repository name.
    - **path**: The file path in the repository.
    """
    return get_file_lines(owner, repo, path)

@router.get("/{owner}/{repo}", summary="Get repository info")
async def get_repository(owner: str, repo: str):
    """
    Fetch detailed information about a repository.
    """
    return get_repo_info(owner, repo)

@router.get("/{owner}/{repo}/contents", summary="List repository contents")
async def get_contents(owner: str, repo: str):
    """
    List all files and directories in the repository.
    """
    return list_repo_contents(owner, repo)

@router.get("/{owner}/{repo}/commits", summary="Get repository commit history")
async def get_commits(owner: str, repo: str):
    """
    Fetch the commit history of the repository.
    """
    return get_commit_history(owner, repo)

@router.get("/{owner}/{repo}/pulls", summary="List pull requests")
async def get_pull_requests(owner: str, repo: str):
    """
    Retrieve the list of pull requests for the repository.
    """
    return list_pull_requests(owner, repo)

@router.get("/{owner}/{repo}/issues", summary="List repository issues")
async def get_issues(owner: str, repo: str):
    """
    Retrieve the list of issues for the repository.
    """
    return list_issues(owner, repo)

@router.get("/{owner}/{repo}/branches", summary="List branches")
async def get_branches(owner: str, repo: str):
    """
    List all branches in the repository.
    """
    return list_branches(owner, repo)
