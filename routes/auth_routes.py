# auth.py - FIXED VERSION with centralized security and strong validation
import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from core import models, schemas
from core.database import get_db
from core.schemas import (
    SignupSchema, LoginSchema, TokenResponse, UserResponse, LogoutResponse,
    BusinessSignupSchema, AddBusinessUserSchema
)
from utils.auth_validators import (
    PasswordValidator, EmailValidator, NameValidator, CompanyValidator, sanitize_input
)
from utils.rate_limiter import (
    check_login_rate_limit, check_signup_rate_limit, 
    login_rate_limiter, signup_rate_limiter, get_client_ip
)
from utils.security_utils import hash_password, verify_password, needs_rehash

# Config - Fail fast if SECRET_KEY is missing in production
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    # Check if we're in development mode
    is_dev = os.environ.get("ENVIRONMENT", "production").lower() in ["development", "dev", "local"]
    if is_dev:
        print("⚠️  WARNING: Using default SECRET_KEY for development. DO NOT use in production!")
        SECRET_KEY = "dev-secret-key-change-in-production-" + os.urandom(32).hex()
    else:
        raise RuntimeError(
            "SECRET_KEY environment variable is required for production. "
            "Generate a secure key with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

router = APIRouter(prefix="/auth", tags=["auth"])

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    now = datetime.utcnow()
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    jti = os.urandom(16).hex()
    to_encode.update({"exp": expire, "iat": now, "jti": jti})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt, jti, expire

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


# ---------- dependencies ----------
def get_current_user(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Get current user from token. Returns None if no valid token.
    Only raises if token is INVALID (not if it's missing).
    """
    if not token:
        return None
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        jti: str = payload.get("jti")
        if user_id is None or jti is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Check if token JTI is revoked
    revoked = db.query(models.RevokedToken).filter(models.RevokedToken.jti == jti).first()
    if revoked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")

    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if user is None:
        raise credentials_exception
    return user


def get_current_active_user(current_user: Optional[models.User] = Depends(get_current_user)):
    """
    Ensures user is authenticated and active.
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if current_user.trial_status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Account is not active"
        )
    return current_user


# ---------- routes ----------
@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupSchema, request: Request, db: Session = Depends(get_db)):
    """User signup - creates account and returns token for auto-login"""
    # Rate limiting
    client_ip = get_client_ip(request)
    check_signup_rate_limit(client_ip)
    
    # Validate inputs
    EmailValidator.validate_or_raise(payload.email)
    PasswordValidator.validate_or_raise(payload.password)
    NameValidator.validate_or_raise(payload.name)
    
    # Sanitize inputs
    email = sanitize_input(payload.email.lower())
    name = sanitize_input(payload.name)
    
    # Check if email already exists
    existing = get_user_by_email(db, email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash password and create user
    hashed_pw = hash_password(payload.password)
    user = models.User(
        email=email,
        password_hash=hashed_pw,
        name=name,
        user_type="free",
        trial_status="active"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Generate token for immediate login
    token_payload = {"user_id": user.user_id, "email": user.email}
    token, jti, expire = create_access_token(token_payload)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.user_id,
            "name": user.name,
            "email": user.email,
            "user_type": user.user_type
        }
    }


@router.post("/login", response_model=TokenResponse)
def login(form_data: LoginSchema, request: Request, db: Session = Depends(get_db)):
    """User login - validates credentials and returns token"""
    # Rate limiting by IP and email
    client_ip = get_client_ip(request)
    email_lower = form_data.email.lower()
    
    check_login_rate_limit(client_ip)
    check_login_rate_limit(email_lower)
    
    # Validate email format
    EmailValidator.validate_or_raise(form_data.email)
    
    user = get_user_by_email(db, email_lower)
    if not user:
        # Record failed attempt
        login_rate_limiter.record_attempt(client_ip)
        login_rate_limiter.record_attempt(email_lower)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Verify password
    password_valid = verify_password(form_data.password, user.password_hash)
    
    if not password_valid:
        # Record failed attempt
        login_rate_limiter.record_attempt(client_ip)
        login_rate_limiter.record_attempt(email_lower)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Clear rate limit on successful login
    login_rate_limiter.clear_attempts(client_ip)
    login_rate_limiter.clear_attempts(email_lower)

    token_payload = {"user_id": user.user_id, "email": user.email}
    token, jti, expire = create_access_token(token_payload)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.user_id,
            "name": user.name,
            "email": user.email,
            "user_type": user.user_type
        }
    }


@router.post("/logout", response_model=LogoutResponse)
def logout(current_user: Optional[models.User] = Depends(get_current_user), 
           token: Optional[str] = Depends(oauth2_scheme),
           db: Session = Depends(get_db)):
    """
    Logout by revoking token. Works even if user is not authenticated.
    """
    if not token:
        # No token = already logged out
        return {"message": "Not logged in", "success": True}
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
        jti = payload.get("jti")
        
        if jti:
            # Check if already revoked
            exists = db.query(models.RevokedToken).filter(models.RevokedToken.jti == jti).first()
            if not exists:
                revoked = models.RevokedToken(jti=jti)
                db.add(revoked)
                db.commit()
        
        return {"message": "Logged out successfully", "success": True}
    except:
        # Token is invalid/expired - just return success
        return {"message": "Logged out", "success": True}


@router.get("/status")
def auth_status(token: Optional[str] = Depends(oauth2_scheme), 
                db: Session = Depends(get_db)):
    """
    Check authentication status. Returns user info if authenticated, 
    or {authenticated: false} if not.
    """
    if not token:
        return {"authenticated": False}
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        jti = payload.get("jti")
        
        if not user_id:
            return {"authenticated": False}
        
        # Check if token is revoked
        revoked = db.query(models.RevokedToken).filter(models.RevokedToken.jti == jti).first()
        if revoked:
            return {"authenticated": False}
        
        # Get user
        user = db.query(models.User).filter(models.User.user_id == user_id).first()
        if not user:
            return {"authenticated": False}

        return {
            "authenticated": True,
            "user": {
                "id": user.user_id,
                "name": user.name,
                "email": user.email
            }
        }
    except Exception as e:
        print(f"Auth status error: {e}")
        return {"authenticated": False}


@router.get("/me", response_model=UserResponse)
def read_me(current_user: models.User = Depends(get_current_active_user)):
    """Get current user profile - requires authentication"""
    return current_user


# ---------- Business Account Routes ----------
@router.post("/business-signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def business_signup(payload: BusinessSignupSchema, request: Request, db: Session = Depends(get_db)):
    """Create a business account with company and admin user"""
    # Rate limiting
    client_ip = get_client_ip(request)
    check_signup_rate_limit(client_ip)
    
    # Validate all inputs
    CompanyValidator.validate_name_or_raise(payload.company_name)
    EmailValidator.validate_or_raise(payload.company_email)
    EmailValidator.validate_or_raise(payload.admin_email)
    PasswordValidator.validate_or_raise(payload.admin_password)
    NameValidator.validate_or_raise(payload.admin_name)
    
    # Sanitize inputs
    company_name = sanitize_input(payload.company_name)
    company_email = sanitize_input(payload.company_email.lower())
    admin_name = sanitize_input(payload.admin_name)
    admin_email = sanitize_input(payload.admin_email.lower())
    admin_password = payload.admin_password
    
    # Check if company already exists
    existing_company = db.query(models.Company).filter(models.Company.name == company_name).first()
    if existing_company:
        raise HTTPException(status_code=400, detail="Company name already exists")
    
    # Check if admin email already exists
    existing_user = get_user_by_email(db, admin_email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create company
    company = models.Company(
        name=company_name,
        contact_email=company_email
    )
    db.add(company)
    db.flush()  # Get company_id without committing
    
    # Create admin user
    hashed_pw = hash_password(admin_password)
    admin_user = models.User(
        email=admin_email,
        password_hash=hashed_pw,
        name=admin_name,
        user_type="b2b_admin",
        trial_status="active",
        company_id=company.company_id
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    
    # Generate token for immediate login
    token_payload = {"user_id": admin_user.user_id, "email": admin_user.email}
    token, jti, expire = create_access_token(token_payload)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": admin_user.user_id,
            "name": admin_user.name,
            "email": admin_user.email,
            "user_type": admin_user.user_type
        }
    }


@router.get("/business-dashboard")
def get_business_dashboard(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get business dashboard data - only for b2b users"""
    if not current_user.company_id:
        raise HTTPException(status_code=403, detail="Not a business account")
    
    if current_user.user_type not in ["b2b_admin", "b2b_employee"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get company
    company = db.query(models.Company).filter(models.Company.company_id == current_user.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Get all users in company
    users = db.query(models.User).filter(models.User.company_id == current_user.company_id).all()
    
    return {
        "company": {
            "id": company.company_id,
            "name": company.name,
            "contact_email": company.contact_email
        },
        "user": {
            "id": current_user.user_id,
            "name": current_user.name,
            "email": current_user.email,
            "user_type": current_user.user_type
        },
        "users": [
            {
                "user_id": u.user_id,
                "name": u.name,
                "email": u.email,
                "user_type": u.user_type,
                "trial_status": u.trial_status,
                "created_at": u.created_at.isoformat() if u.created_at else None
            }
            for u in users
        ]
    }


@router.post("/add-business-user", status_code=status.HTTP_201_CREATED)
def add_business_user(
    payload: AddBusinessUserSchema,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add a new user to the business account - admin only"""
    # Validate inputs
    NameValidator.validate_or_raise(payload.name)
    EmailValidator.validate_or_raise(payload.email)
    PasswordValidator.validate_or_raise(payload.password)
    
    # Sanitize inputs
    name = sanitize_input(payload.name)
    email = sanitize_input(payload.email.lower())
    password = payload.password
    user_type = payload.user_type
    
    # Check if current user is admin
    if current_user.user_type != "b2b_admin":
        raise HTTPException(status_code=403, detail="Only admins can add users")
    
    if not current_user.company_id:
        raise HTTPException(status_code=403, detail="Not a business account")
    
    # Get company to validate email domain
    company = db.query(models.Company).filter(models.Company.company_id == current_user.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Extract domain from company email
    company_domain = company.contact_email.split('@')[1] if '@' in company.contact_email else None
    if not company_domain:
        raise HTTPException(status_code=400, detail="Invalid company email format")
    
    # Validate employee email domain matches company domain
    employee_domain = email.split('@')[1] if '@' in email else None
    if not employee_domain or employee_domain != company_domain:
        raise HTTPException(
            status_code=400, 
            detail=f"Employee email must use company domain: @{company_domain}"
        )
    
    # Validate user_type
    if user_type not in ["b2b_employee", "b2b_admin"]:
        raise HTTPException(status_code=400, detail="Invalid user type")
    
    # Check if email already exists
    existing_user = get_user_by_email(db, email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_pw = hash_password(password)
    new_user = models.User(
        email=email,
        password_hash=hashed_pw,
        name=name,
        user_type=user_type,
        trial_status="active",
        company_id=current_user.company_id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "message": "User added successfully",
        "user": {
            "id": new_user.user_id,
            "name": new_user.name,
            "email": new_user.email,
            "user_type": new_user.user_type
        }
    }


@router.delete("/delete-business-user/{user_id}")
def delete_business_user(
    user_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a user from the business account - admin only"""
    # Check if current user is admin
    if current_user.user_type != "b2b_admin":
        raise HTTPException(status_code=403, detail="Only admins can delete users")
    
    if not current_user.company_id:
        raise HTTPException(status_code=403, detail="Not a business account")
    
    # Get user to delete
    user_to_delete = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user belongs to same company
    if user_to_delete.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="User does not belong to your company")
    
    # Prevent deleting yourself
    if user_to_delete.user_id == current_user.user_id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    # Delete user
    db.delete(user_to_delete)
    db.commit()
    
    return {"message": "User deleted successfully"}