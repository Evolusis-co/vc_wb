from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from .auth_utils import SECRET_KEY, ALGORITHM
from core.database import get_db
from sqlalchemy.orm import Session
from core.models import User
from .token_blacklist import is_blacklisted
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

# Import token blacklist from auth_routes
# from routes.auth_routes import token_blacklist

async def get_token(request: Request) -> str:
    """Extract token from header or cookie"""
    # Try to get from Authorization header first
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]
    
    # Try to get from cookie
    token = request.cookies.get("access_token")
    if token:
        return token
    
    return None

def get_current_user(
    request: Request = None,
    token: str = Depends(get_token),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        raise credentials_exception
    
    # Check if token is blacklisted
    if is_blacklisted(token):  # Use the function instead of direct access
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked"
        )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except JWTError as e:
        print(f"JWT Error: {e}")
        raise credentials_exception

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise credentials_exception
        
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.trial_status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Account is not active"
        )
    return current_user

def get_premium_user(current_user: User = Depends(get_current_active_user)):
    if current_user.user_type not in ["premium", "premium_pro", "b2b_employee", "b2b_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium feature required"
        )
    return current_user