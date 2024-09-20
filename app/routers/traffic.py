# app/routers/traffic.py
# Router file handling traffic-related operations (views and clones).

from fastapi import APIRouter, Path
from services.github_service import github_request

router = APIRouter(
    prefix="/traffic",
    tags=["traffic"],
    responses={404: {"description": "Not found"}}
)

@router.get("/repo/{owner}/{repo}/views", summary="Retrieve repository traffic views",
            description="Get the number of views for the repository over a specified time period.")
def get_repo_traffic_views(owner: str = Path(..., description="GitHub username or organization"),
                           repo: str = Path(..., description="Repository name")):
    endpoint = f"repos/{owner}/{repo}/traffic/views"
    return github_request(endpoint)

@router.get("/repo/{owner}/{repo}/clones", summary="Retrieve repository traffic clones",
            description="Get the number of times the repository has been cloned over a specified time period.")
def get_repo_traffic_clones(owner: str = Path(..., description="GitHub username or organization"),
                            repo: str = Path(..., description="Repository name")):
    endpoint = f"repos/{owner}/{repo}/traffic/clones"
    return github_request(endpoint)
