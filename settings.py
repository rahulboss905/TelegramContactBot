import os

# load environment variables
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GROUP_ID = os.getenv('TELEGRAM_GROUP_ID')

# anti-flood constants
MAX_FLOOD_ATTEMPTS = 20  # times before ban for flooding in general
FLOOD_DETECTION_INTERVAL = 20 # Seconds

# other constants
BANNED_USER_DB = 'banned.txt' # Banned users db
LOG_FILE_PATH = 'bot_log.txt' # Log file path
LOG_MAX_SIZE = 100 * 1024 * 1024 # Log file max size in bits
RELOAD_TIME = 7200 # When to reload banned list file in secons (7200s=2h)

# help message text
HLP_MSG = 'Just type and send your message and it will be sent to bot admin(s). You can only send TEXT and emoji messages, so no sticker, GIFs and etc. are allowed. Flooding the bot automatically bans you from using the bot.'
