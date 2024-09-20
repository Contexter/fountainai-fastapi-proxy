# app/services/logging_service.py
# Service file for committing and pushing logs to GitHub.

import os
from datetime import datetime
from fastapi import HTTPException

def commit_and_push_logs():
    try:
        repo_path = os.getcwd()
        if not os.path.exists(os.path.join(repo_path, '.git')):
            raise Exception("Current directory is not a Git repository.")

        commit_message = f"Log update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        os.system('git add app.log')
        os.system(f'git commit -m "${commit_message}"')
        os.system('git push origin main')

        return "Logs have been successfully committed and pushed to GitHub."
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error committing logs: {str(e)}")
