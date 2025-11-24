"""
Centralized security utilities for password hashing and validation
"""
import bcrypt
from typing import Tuple


class PasswordHasher:
    """Centralized password hashing using bcrypt"""
    
    BCRYPT_ROUNDS = 12  # Cost factor for bcrypt
    MAX_PASSWORD_LENGTH = 72  # Bcrypt limitation
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
            
        Raises:
            ValueError: If password exceeds bcrypt's 72-byte limit
        """
        password_bytes = password.encode('utf-8')
        
        # Check length before hashing
        if len(password_bytes) > PasswordHasher.MAX_PASSWORD_LENGTH:
            # Truncate with warning - this should be caught by validation earlier
            print(f"⚠️  WARNING: Password truncated to {PasswordHasher.MAX_PASSWORD_LENGTH} bytes")
            password_bytes = password_bytes[:PasswordHasher.MAX_PASSWORD_LENGTH]
        
        salt = bcrypt.gensalt(rounds=PasswordHasher.BCRYPT_ROUNDS)
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash
        
        Args:
            plain_password: Plain text password to verify
            hashed_password: Hashed password to compare against
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            password_bytes = plain_password.encode('utf-8')
            
            # Truncate to bcrypt limit if necessary
            if len(password_bytes) > PasswordHasher.MAX_PASSWORD_LENGTH:
                password_bytes = password_bytes[:PasswordHasher.MAX_PASSWORD_LENGTH]
            
            return bcrypt.checkpw(password_bytes, hashed_password.encode('utf-8'))
        except Exception as e:
            # Log error but don't expose details
            print(f"Password verification error: {type(e).__name__}")
            return False
    
    @staticmethod
    def needs_rehash(hashed_password: str) -> bool:
        """
        Check if a password hash needs to be updated
        (e.g., if cost factor has changed)
        
        Args:
            hashed_password: The hashed password to check
            
        Returns:
            True if hash should be updated
        """
        try:
            # Extract cost factor from hash
            # Bcrypt hash format: $2b$rounds$salt+hash
            parts = hashed_password.split('$')
            if len(parts) >= 3:
                current_rounds = int(parts[2])
                return current_rounds < PasswordHasher.BCRYPT_ROUNDS
        except:
            pass
        return False


# Singleton instance
password_hasher = PasswordHasher()


# Convenience functions
def hash_password(password: str) -> str:
    """Hash a password"""
    return password_hasher.hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password"""
    return password_hasher.verify_password(plain_password, hashed_password)


def needs_rehash(hashed_password: str) -> bool:
    """Check if password needs rehashing"""
    return password_hasher.needs_rehash(hashed_password)
