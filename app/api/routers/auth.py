from fastapi import APIRouter

from app.api.dependencies import AuthServiceDep
from app.api.schemas.auth import RefreshTokenRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    payload: RefreshTokenRequest,
    service: AuthServiceDep,
):
    return await service.refresh(payload.refresh_token)
