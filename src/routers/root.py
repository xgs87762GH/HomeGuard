from fastapi import APIRouter

router = APIRouter(tags=["Root"])

@router.get("/")
async def root():
    return {"message": "Hello HomeGuard"}



