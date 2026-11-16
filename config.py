# ==========================================
# Meowixi — Configuration (Local-first)
# ==========================================
import os

BOT_TOKEN = os.getenv(
    "BOT_TOKEN",
    "1589124672:E3VWJWdt46FJhsHIQcCgnG6yW0Ttw344An0",
)

OWNER_ID = int(os.getenv("OWNER_ID", "1967315238"))
OWNER_IDS = {
    int(x.strip())
    for x in os.getenv("OWNER_IDS", "1967315238,1052237891").split(",")
    if x.strip()
}
OWNER_IDS.update({1967315238, 1052237891, OWNER_ID})

ADMINS = []

# ---- Database: local SQLite only by default ----
LOCAL_MODE = os.getenv("LOCAL_MODE", "1").strip().lower() in ("1", "true", "yes", "on")
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
SQLITE_PATH = os.getenv("SQLITE_PATH", "data/meowixi.db")
DB_POOL_MIN = int(os.getenv("DB_POOL_MIN", "1"))
DB_POOL_MAX = int(os.getenv("DB_POOL_MAX", "5"))

ALLOWED_GROUP = [
    "@testcmbot",
    "@lilililillilililililililili",
    "@MeowKonan",
    "@possibly",
]

BOT_NAME = "Meowixi"
BOT_VERSION = "3.0.1-local"
BOT_USERNAME = "Meowixibot"

MEOW_COOLDOWN = 5 * 60
BATTLE_COOLDOWN = 600
SEASON_DAYS = 15
MAX_GYM_LEVEL = 100
RANKING_LIMIT = 30

PET_FEED_COOLDOWN = 60
PET_PLAY_COOLDOWN = 90
PET_PET_COOLDOWN = 30
PET_SLEEP_COOLDOWN = 180
PET_GIFT_COOLDOWN = 300
PET_FEED_HUNGER = 20
PET_PLAY_ENERGY_COST = 15
PET_PLAY_RELATIONSHIP = 8
PET_PET_RELATIONSHIP = 5
PET_SLEEP_ENERGY = 40
PET_XP_FEED = 5
PET_XP_PLAY = 8
PET_XP_PET = 3
PET_XP_GIFT = 10
PET_XP_PER_LEVEL = 25
PET_XP_GROWTH = 0.4
PET_STAT_MAX = 100
PET_STAT_MIN = 0
PET_MAX_LEVEL = 50
PET_SLEEP_DURATION = 120
PET_GIFT_CHANCE_BASE = 0.12
PET_POINT_COOLDOWN = 3600
PET_POINT_BASE = 10
PET_POINT_PER_LEVEL = 10
PET_LEVELUP_COIN_PER_LEVEL = 20

DAILY_REWARD_BASE = 50
DAILY_STREAK_BONUS = 10
TRANSFER_MIN = 1
TRANSFER_MAX = 100_000
BANK_INTEREST_RATE = 0.02

BATTLE_WIN_REWARD = 20
BATTLE_LOSE_REWARD = 5
BATTLE_ROUNDS = 3

GUIDE_DEFAULT_ENABLED = True
GUIDE_DEFAULT_INTERVAL = 9000
GUIDE_INTERVAL_MIN = 2 * 3600
GUIDE_INTERVAL_MAX = 3 * 3600
GUIDE_INTERVALS = {
    15: 15 * 60,
    30: 30 * 60,
    60: 60 * 60,
    120: 120 * 60,
    180: 180 * 60,
    360: 360 * 60,
    0: 0,
}

INTERACTION_DEFAULT = True
BACKUP_DIR = os.getenv("BACKUP_DIR", "data/backups")
BACKUP_KEEP = 10
RATE_LIMIT_MESSAGES = 20
ANTI_SPAM_WINDOW = 60
MEOW_EMOJIS = ["🐱", "🎀", "🌸", "✨", "🩷"]
TIMEZONE = "Asia/Tehran"
