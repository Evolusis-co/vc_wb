"""
Flask-compatible authentication validators (adapted from voiceCoach)
"""
import re
from typing import Tuple


class PasswordValidationError(ValueError):
    pass

class EmailValidationError(ValueError):
    pass

class NameValidationError(ValueError):
    pass

class CompanyValidationError(ValueError):
    pass


class PasswordValidator:
    """Validate password strength"""
    MIN_LENGTH = 8
    MAX_LENGTH = 128

    @staticmethod
    def validate(password: str) -> Tuple[bool, str]:
        if not password:
            return False, "Password is required"

        if len(password) < PasswordValidator.MIN_LENGTH:
            return False, f"Password must be at least {PasswordValidator.MIN_LENGTH} characters"

        if len(password) > PasswordValidator.MAX_LENGTH:
            return False, f"Password must not exceed {PasswordValidator.MAX_LENGTH} characters"

        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"

        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"

        if not re.search(r'\d', password):
            return False, "Password must contain at least one number"

        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\/;~`]', password):
            return False, "Password must contain at least one special character (!@#$%^&*...)"

        weak_passwords = [
            'password', 'password123', '12345678', 'qwerty123',
            'admin123', 'letmein', 'welcome123', 'monkey123'
        ]
        if password.lower() in weak_passwords:
            return False, "Password is too common. Please choose a stronger password"

        return True, ""

    @staticmethod
    def validate_or_raise(password: str):
        is_valid, error_msg = PasswordValidator.validate(password)
        if not is_valid:
            raise PasswordValidationError(error_msg)


class EmailValidator:
    """Validate email format and security"""
    DISPOSABLE_DOMAINS = [
        'tempmail.com', 'throwaway.email', '10minutemail.com',
        'guerrillamail.com', 'mailinator.com', 'trashmail.com',
        'fakeinbox.com', 'yopmail.com', 'temp-mail.org'
    ]

    @staticmethod
    def validate(email: str) -> Tuple[bool, str]:
        if not email:
            return False, "Email is required"

        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return False, "Invalid email format"

        if len(email) > 254:
            return False, "Email address is too long"

        domain = email.split('@')[1].lower()
        if domain in EmailValidator.DISPOSABLE_DOMAINS:
            return False, "Disposable email addresses are not allowed"

        if '..' in email or email.startswith('.') or email.endswith('.'):
            return False, "Invalid email format"

        return True, ""

    @staticmethod
    def validate_or_raise(email: str):
        is_valid, error_msg = EmailValidator.validate(email)
        if not is_valid:
            raise EmailValidationError(error_msg)


class NameValidator:
    MIN_LENGTH = 2
    MAX_LENGTH = 100

    @staticmethod
    def validate(name: str) -> Tuple[bool, str]:
        if not name or not name.strip():
            return False, "Name is required"

        name = name.strip()

        if len(name) < NameValidator.MIN_LENGTH:
            return False, f"Name must be at least {NameValidator.MIN_LENGTH} characters"

        if len(name) > NameValidator.MAX_LENGTH:
            return False, f"Name must not exceed {NameValidator.MAX_LENGTH} characters"

        if not re.match(r"^[a-zA-Z\s\-'\.]+$", name):
            return False, "Name can only contain letters, spaces, hyphens, and apostrophes"

        if re.search(r'(.)\1{4,}', name):
            return False, "Name contains invalid pattern"

        return True, ""

    @staticmethod
    def validate_or_raise(name: str):
        is_valid, error_msg = NameValidator.validate(name)
        if not is_valid:
            raise NameValidationError(error_msg)


class CompanyValidator:
    MIN_NAME_LENGTH = 2
    MAX_NAME_LENGTH = 200

    @staticmethod
    def validate_name(company_name: str) -> Tuple[bool, str]:
        if not company_name or not company_name.strip():
            return False, "Company name is required"

        company_name = company_name.strip()

        if len(company_name) < CompanyValidator.MIN_NAME_LENGTH:
            return False, f"Company name must be at least {CompanyValidator.MIN_NAME_LENGTH} characters"

        if len(company_name) > CompanyValidator.MAX_NAME_LENGTH:
            return False, f"Company name must not exceed {CompanyValidator.MAX_NAME_LENGTH} characters"

        if not re.match(r"^[a-zA-Z0-9\s\-'&.,()]+$", company_name):
            return False, "Company name contains invalid characters"

        return True, ""

    @staticmethod
    def validate_name_or_raise(company_name: str):
        is_valid, error_msg = CompanyValidator.validate_name(company_name)
        if not is_valid:
            raise CompanyValidationError(error_msg)


def sanitize_input(text: str) -> str:
    if not text:
        return text

    text = re.sub(r'<[^>]*>', '', text)
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)

    sql_patterns = [
        r'(\bUNION\b|\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bDROP\b)',
        r'(--|;|/\*|\*/)',
        r'(\bOR\b\s+\d+\s*=\s*\d+)',
        r'(\bAND\b\s+\d+\s*=\s*\d+)'
    ]

    for pattern in sql_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            raise ValueError("Invalid input detected")

    return text.strip()
