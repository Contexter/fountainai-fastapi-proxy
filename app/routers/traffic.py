from fastapi import APIRouter
from app.services.github_service import get_traffic_views, get_traffic_clones

router = APIRouter(
    prefix="/traffic",
    tags=["Traffic"],
    responses={404: {"description": "Not found"}},
)

@router.get("/{owner}/{repo}/views", summary="Get traffic views")
async def get_views(owner: str, repo: str):
    """
    Get the number of views for a repository over a specific time period.
    """
    return get_traffic_views(owner, repo)

@router.get("/{owner}/{repo}/clones", summary="Get traffic clones")
async def get_clones(owner: str, repo: str):
    """
    Get the number of times the repository has been cloned.
    """
    return get_traffic_clones(owner, repo)
