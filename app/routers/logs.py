from fastapi import APIRouter
from app.services.github_service import push_logs_to_github

router = APIRouter(
    prefix="/logs",
    tags=["Logs"],
    responses={404: {"description": "Not found"}},
)

@router.get("/push-logs", summary="Push logs to GitHub")
async def push_logs():
    """
    Push application logs to the configured GitHub repository.
    
    This endpoint triggers log collection and pushes them to GitHub for auditing.
    """
    return push_logs_to_github()
