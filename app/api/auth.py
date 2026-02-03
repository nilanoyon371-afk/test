from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import secrets

from app.core.database import get_db
from app.core.auth import create_access_token, get_password_hash
from app.models.models import User
from app.models.schemas import Token

router = APIRouter()

class GuestLoginRequest(BaseModel):
    device_id: str

@router.post("/guest-login", response_model=Token)
async def guest_login(
    request: GuestLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login or Register a persistent Guest User by unique Device ID.
    If the device ID exists, logs them in.
    If not, creates a new Guest User account.
    """
    if not request.device_id or len(request.device_id) < 5:
        raise HTTPException(status_code=400, detail="Invalid device ID")

    # Check if user with this device_id exists
    result = await db.execute(select(User).filter(User.device_id == request.device_id))
    user = result.scalar_one_or_none()

    if not user:
        # Create new Guest User
        # We generate a random placeholder email/password for internal consistency
        random_suffix = secrets.token_hex(4)
        new_username = f"Guest-{random_suffix}"
        backup_email = f"{request.device_id}@guest.local"
        
        # Ensure email/username uniqueness (unlikely collision but good practice)
        while True:
            existing = await db.execute(select(User).filter(User.username == new_username))
            if not existing.scalar_one_or_none():
                break
            random_suffix = secrets.token_hex(4)
            new_username = f"Guest-{random_suffix}"

        user = User(
            email=backup_email,
            username=new_username,
            hashed_password=get_password_hash(secrets.token_urlsafe(32)), # Unusable password
            device_id=request.device_id,
            role="guest",
            is_active=True,
            daily_quota=5000 # Higher quota for app users
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # Generate Token
    access_token = create_access_token(data={"sub": user.id, "role": user.role})
    
    return Token(
        access_token=access_token,
        token_type="bearer"
    )
