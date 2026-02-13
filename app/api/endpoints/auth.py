from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta
import uuid

from app.core.database import get_db
from app.core.auth import create_access_token, create_refresh_token
from app.models.models import User
from app.models.schemas import GuestLoginRequest, GuestLoginResponse, TokenResponse, UserResponse
from app.config.settings import settings

router = APIRouter()

@router.post("/guest", response_model=GuestLoginResponse)
async def guest_login(
    body: GuestLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register or login a guest user based on device_id.
    1 Device = 1 Account.
    """
    # 1. Check if user already exists with this device_id
    result = await db.execute(select(User).filter(User.device_id == body.device_id))
    user = result.scalar_one_or_none()
    
    if not user:
        # 2. Create new guest user
        # Use a placeholder email since it's required and unique
        placeholder_email = f"guest_{body.device_id[:16]}_{uuid.uuid4().hex[:8]}@apphub.internal"
        
        # Generate a random username or use device name if provided
        username = body.device_name or f"Guest_{body.device_id[:8]}"
        
        user = User(
            email=placeholder_email,
            username=username,
            hashed_password="!", # Guest accounts don't use passwords
            device_id=body.device_id,
            role="guest",
            is_active=True,
            daily_quota=500 # Slightly lower quota for guests?
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
    
    # 3. Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    token_response = TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    return GuestLoginResponse(
        token=token_response,
        user=UserResponse.from_orm(user)
    )
