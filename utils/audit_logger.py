"""
Audit logging for security events and DPDP compliance
"""
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class AuditEventType(Enum):
    """Types of audit events"""
    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    SIGNUP = "signup"
    TOKEN_CREATED = "token_created"
    TOKEN_REVOKED = "token_revoked"
    
    # Authorization events
    ACCESS_DENIED = "access_denied"
    PERMISSION_GRANTED = "permission_granted"
    
    # Data access events
    DATA_READ = "data_read"
    DATA_CREATED = "data_created"
    DATA_UPDATED = "data_updated"
    DATA_DELETED = "data_deleted"
    
    # Security events
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    PASSWORD_CHANGED = "password_changed"
    
    # Business events
    USER_ADDED = "user_added"
    USER_REMOVED = "user_removed"
    COMPANY_CREATED = "company_created"


class AuditLogger:
    """Centralized audit logging"""
    
    def __init__(self):
        # Configure audit logger
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)
        
        # Create file handler for audit logs
        handler = logging.FileHandler("audit.log")
        handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
    
    def log_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True
    ):
        """
        Log an audit event
        
        Args:
            event_type: Type of event
            user_id: User ID if applicable
            user_email: User email (will be redacted in logs)
            ip_address: Client IP address
            details: Additional event details
            success: Whether the event was successful
        """
        # Redact sensitive information
        safe_email = self._redact_email(user_email) if user_email else None
        safe_details = self._redact_sensitive_data(details) if details else {}
        
        event_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type.value,
            "user_id": user_id,
            "user_email": safe_email,
            "ip_address": ip_address,
            "success": success,
            "details": safe_details
        }
        
        # Log as JSON for easy parsing
        self.logger.info(json.dumps(event_data))
    
    def log_login_attempt(
        self,
        email: str,
        ip_address: str,
        success: bool,
        failure_reason: Optional[str] = None
    ):
        """Log a login attempt"""
        event_type = AuditEventType.LOGIN_SUCCESS if success else AuditEventType.LOGIN_FAILED
        details = {"failure_reason": failure_reason} if failure_reason else {}
        
        self.log_event(
            event_type=event_type,
            user_email=email,
            ip_address=ip_address,
            details=details,
            success=success
        )
    
    def log_token_creation(
        self,
        user_id: int,
        user_email: str,
        jti: str,
        expires_at: datetime,
        ip_address: Optional[str] = None
    ):
        """Log JWT token creation"""
        self.log_event(
            event_type=AuditEventType.TOKEN_CREATED,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            details={
                "jti": jti,
                "expires_at": expires_at.isoformat()
            }
        )
    
    def log_data_access(
        self,
        user_id: int,
        resource_type: str,
        resource_id: Optional[int] = None,
        action: str = "read",
        ip_address: Optional[str] = None
    ):
        """Log data access for DPDP compliance"""
        self.log_event(
            event_type=AuditEventType.DATA_READ,
            user_id=user_id,
            ip_address=ip_address,
            details={
                "resource_type": resource_type,
                "resource_id": resource_id,
                "action": action
            }
        )
    
    def log_rate_limit_exceeded(
        self,
        identifier: str,
        ip_address: str,
        endpoint: str
    ):
        """Log rate limit exceeded"""
        self.log_event(
            event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
            ip_address=ip_address,
            details={
                "identifier": identifier,
                "endpoint": endpoint
            },
            success=False
        )
    
    @staticmethod
    def _redact_email(email: str) -> str:
        """Redact email for logging (keep domain)"""
        if '@' in email:
            local, domain = email.split('@', 1)
            if len(local) > 2:
                redacted_local = local[0] + '*' * (len(local) - 2) + local[-1]
            else:
                redacted_local = '*' * len(local)
            return f"{redacted_local}@{domain}"
        return "***"
    
    @staticmethod
    def _redact_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Redact sensitive fields from data"""
        sensitive_keys = ['password', 'token', 'secret', 'api_key', 'credit_card']
        
        redacted = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                redacted[key] = "***REDACTED***"
            elif isinstance(value, dict):
                redacted[key] = AuditLogger._redact_sensitive_data(value)
            else:
                redacted[key] = value
        
        return redacted


# Global audit logger instance
audit_logger = AuditLogger()
