import os

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = os.getenv('REDIS_PORT', '6379')
REDIS_DB = 0
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

REDIS_CHAT_HISTORY_KEY_PREFIX = "agent:chat:history:"
CHAT_SESSION_EXPIRE = 86400
