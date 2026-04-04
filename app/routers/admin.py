from fastapi import APIRouter

router = APIRouter(tags=["admin"])


@router.get("/stats")
async def stats():
    return {"message": "DarkVPN admin panel"}