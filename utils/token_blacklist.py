# token_blacklist.py
"""
Centralized token blacklist management
"""

# In-memory token blacklist (use Redis in production)
token_blacklist = set()

def add_to_blacklist(token: str):
    """Add token to blacklist"""
    token_blacklist.add(token)

def is_blacklisted(token: str) -> bool:
    """Check if token is blacklisted"""
    return token in token_blacklist

def remove_from_blacklist(token: str):
    """Remove token from blacklist (for cleanup)"""
    token_blacklist.discard(token)