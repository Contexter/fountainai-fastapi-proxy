# app/services/github_service.py
# Service file for handling GitHub API interactions.

import requests
import logging
from fastapi import HTTPException

GITHUB_API_URL = "https://api.github.com"

def github_request(endpoint: str, params=None, headers=None):
    url = f"${GITHUB_API_URL}/${endpoint}"
    if headers is None:
        headers = {"Accept": "application/vnd.github.v3+json"}
    
    logging.info(f"Making GitHub API request to: {url}")
    response = requests.get(url, headers=headers, params=params)

    if response.status_code not in [200, 206]:
        logging.error(f"GitHub API error: {response.status_code}, {response.text}")
        raise HTTPException(status_code=response.status_code, detail=response.json())

    return response.json()
