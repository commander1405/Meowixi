# ==========================================
# Bot key-value settings (GLOBAL_MEOW_GROUP etc.)
# ==========================================

from .pool import fetchrow, execute, fetchval


async def ensure_settings_table():
    """Create bot_settings — SQLite-safe (no DEFAULT (datetime))."""
    try:
        await execute(
            """
            CREATE TABLE IF NOT EXISTS bot_settings (
                key TEXT PRIMARY KEY,
                value TEXT DEFAULT '',
                updated_at TEXT
            )
            """
        )
    except Exception as e:
        print(f"ensure_settings_table: {e}")


async def get_setting(key: str, default=None):
    await ensure_settings_table()
    try:
        val = await fetchval("SELECT value FROM bot_settings WHERE key = $1", str(key))
    except Exception as e:
        print(f"get_setting({key}): {e}")
        return default
    if val is None:
        return default
    return str(val)


async def set_setting(key: str, value: str):
    await ensure_settings_table()
    v = "" if value is None else str(value)
    try:
        from config import LOCAL_MODE
    except Exception:
        LOCAL_MODE = True
    if LOCAL_MODE:
        await execute(
            """
            INSERT INTO bot_settings (key, value, updated_at)
            VALUES ($1, $2, datetime('now'))
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = datetime('now')
            """,
            str(key), v,
        )
    else:
        await execute(
            """
            INSERT INTO bot_settings (key, value, updated_at)
            VALUES ($1, $2, NOW())
            ON CONFLICT (key) DO UPDATE SET
                value = EXCLUDED.value,
                updated_at = NOW()
            """,
            str(key), v,
        )


async def get_global_meow_group():
    chat_id = await get_setting("global_meow_group_id", "")
    invite = await get_setting("global_meow_invite", "")
    title = await get_setting("global_meow_title", "گروه میو")
    if not chat_id:
        return None
    return {
        "chat_id": str(chat_id),
        "invite_link": str(invite or ""),
        "title": str(title or "گروه میو"),
    }


async def set_global_meow_group(chat_id: str, invite_link: str = "", title: str = ""):
    await set_setting("global_meow_group_id", str(chat_id).strip())
    await set_setting("global_meow_invite", str(invite_link or "").strip())
    await set_setting("global_meow_title", str(title or "گروه میو").strip())
