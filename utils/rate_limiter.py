"""
Rate limiter for authentication endpoints
"""
import time
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import HTTPException, status, Request


class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        # Store: {identifier: [(timestamp, count)]}
        self.attempts: Dict[str, list] = defaultdict(list)
        self.lockouts: Dict[str, float] = {}  # {identifier: lockout_until_timestamp}
    
    def check_rate_limit(
        self, 
        identifier: str, 
        max_attempts: int = 5, 
        window_seconds: int = 300,  # 5 minutes
        lockout_seconds: int = 900  # 15 minutes
    ) -> Tuple[bool, str]:
        """
        Check if identifier has exceeded rate limit
        Returns: (is_allowed, error_message)
        """
        current_time = time.time()
        
        # Check if currently locked out
        if identifier in self.lockouts:
            lockout_until = self.lockouts[identifier]
            if current_time < lockout_until:
                remaining = int(lockout_until - current_time)
                minutes = remaining // 60
                seconds = remaining % 60
                return False, f"Too many failed attempts. Try again in {minutes}m {seconds}s"
            else:
                # Lockout expired, remove it
                del self.lockouts[identifier]
                self.attempts[identifier] = []
        
        # Clean old attempts outside the window
        self.attempts[identifier] = [
            timestamp for timestamp in self.attempts[identifier]
            if current_time - timestamp < window_seconds
        ]
        
        # Check if exceeded max attempts
        if len(self.attempts[identifier]) >= max_attempts:
            # Lock out the user
            self.lockouts[identifier] = current_time + lockout_seconds
            self.attempts[identifier] = []
            return False, f"Too many failed attempts. Account locked for {lockout_seconds // 60} minutes"
        
        return True, ""
    
    def record_attempt(self, identifier: str):
        """Record a failed attempt"""
        self.attempts[identifier].append(time.time())
    
    def clear_attempts(self, identifier: str):
        """Clear attempts for identifier (on successful login)"""
        if identifier in self.attempts:
            del self.attempts[identifier]
        if identifier in self.lockouts:
            del self.lockouts[identifier]
    
    def cleanup_old_entries(self, max_age_seconds: int = 3600):
        """Clean up old entries to prevent memory bloat"""
        current_time = time.time()
        
        # Clean attempts
        identifiers_to_remove = []
        for identifier, timestamps in self.attempts.items():
            # Remove old timestamps
            self.attempts[identifier] = [
                ts for ts in timestamps 
                if current_time - ts < max_age_seconds
            ]
            # If no timestamps left, mark for removal
            if not self.attempts[identifier]:
                identifiers_to_remove.append(identifier)
        
        for identifier in identifiers_to_remove:
            del self.attempts[identifier]
        
        # Clean expired lockouts
        lockouts_to_remove = [
            identifier for identifier, lockout_until in self.lockouts.items()
            if current_time > lockout_until
        ]
        for identifier in lockouts_to_remove:
            del self.lockouts[identifier]


# Global rate limiter instance
login_rate_limiter = RateLimiter()
signup_rate_limiter = RateLimiter()


def check_login_rate_limit(identifier: str):
    """Check login rate limit and raise exception if exceeded"""
    is_allowed, error_msg = login_rate_limiter.check_rate_limit(
        identifier,
        max_attempts=5,
        window_seconds=300,  # 5 minutes
        lockout_seconds=900  # 15 minutes
    )
    
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=error_msg
        )


def check_signup_rate_limit(identifier: str):
    """Check signup rate limit and raise exception if exceeded"""
    is_allowed, error_msg = signup_rate_limiter.check_rate_limit(
        identifier,
        max_attempts=3,
        window_seconds=3600,  # 1 hour
        lockout_seconds=3600  # 1 hour
    )
    
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=error_msg
        )


def get_client_ip(request: Request) -> str:
    """Get client IP address from request"""
    # Check for forwarded IP (if behind proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    # Check for real IP
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to client host
    if request.client:
        return request.client.host
    
    return "unknown"
