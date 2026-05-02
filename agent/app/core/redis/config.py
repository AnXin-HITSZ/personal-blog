import os
from urllib.parse import urlparse


_redis_url = os.getenv('REDIS_URL')
if _redis_url:
    parsed = urlparse(_redis_url)
    REDIS_HOST = parsed.hostname or 'localhost'
    REDIS_PORT = str(parsed.port or 6379)
    REDIS_DB = int((parsed.path or '/0').lstrip('/') or 0)
    REDIS_PASSWORD = parsed.password
else:
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = os.getenv('REDIS_PORT', '6379')
    REDIS_DB = 0
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

REDIS_CHAT_HISTORY_KEY_PREFIX = "agent:chat:history:"
CHAT_SESSION_EXPIRE = 86400
