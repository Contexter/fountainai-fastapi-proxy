# app/routers/logs.py
# Router file handling log-related operations (committing and pushing logs to GitHub).

from fastapi import APIRouter, HTTPException
from services.logging_service import commit_and_push_logs

router = APIRouter(
    prefix="/logs",
    tags=["logs"],
    responses={404: {"description": "Not found"}}
)

@router.get("/push", summary="Push logs to GitHub",
            description="Triggers a log commit and pushes it to GitHub.")
async def push_logs():
    try:
        message = commit_and_push_logs()
        return {"message": message}
    except HTTPException as e:
        return {"error": e.detail}
