"""
Redis client is configured centrally in app/database.py.
Import redis_client from there:

    from ..database import redis_client
"""
from .database import redis_client  # re-export for convenience

__all__ = ["redis_client"]
