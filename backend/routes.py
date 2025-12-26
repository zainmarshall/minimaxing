# This file can be used to define API endpoints related to chess logic, matchmaking, etc.

from fastapi import APIRouter

router = APIRouter()

@router.get("/status")
def get_status():
    return {"status": "Backend is running"}
