"""
مدیریت دکمه تبلیغ — پورت از MEGA BOT (تک‌دکمه title+url+enabled).
ذخیره در bot_settings؛ فقط Owner.
"""
from __future__ import annotations
import logging
import time
from bale import InlineKeyboardMarkup, InlineKeyboardButton

from database.settings import get_setting, set_setting

logger = logging.getLogger("meowbot.ads")

# cache 30s مثل MEGA
_ad_cache: tuple[bool, str, str] | None = None
_ad_cache_ts: float = 0.0


def _kb(rows) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    rn = 1
    for row in rows:
        if not row:
            continue
        for text, data in row:
            kb.add(InlineKeyboardButton(text=str(text)[:64], callback_data=str(data)[:64]), row=rn)
        rn += 1
    return kb


def invalidate_ad_cache() -> None:
    global _ad_cache, _ad_cache_ts
    _ad_cache = None
    _ad_cache_ts = 0.0


async def get_ad_config() -> tuple[bool, str, str]:
    """(enabled, url, title) — کش ۳۰ ثانیه."""
    global _ad_cache, _ad_cache_ts
    now = time.time()
    if _ad_cache is not None and (now - _ad_cache_ts) < 30:
        return _ad_cache
    try:
        raw_en = await get_setting("ad_enabled", "0")
        enabled = str(raw_en or "").strip().lower() in ("1", "true", "yes", "on")
        url = str(await get_setting("ad_url", "") or "").strip()
        title = str(await get_setting("ad_title", "") or "").strip()
    except Exception as e:
        logger.warning("get_ad_config: %s", e)
        enabled, url, title = False, "", ""
    _ad_cache = (enabled, url, title)
    _ad_cache_ts = now
    return _ad_cache


async def set_ad_enabled(on: bool) -> None:
    await set_setting("ad_enabled", "1" if on else "0")
    invalidate_ad_cache()
    try:
        from utils.ui_helpers import update_promo_snapshot, DEFAULT_CHANNEL_URL, DEFAULT_CHANNEL_TITLE
        enabled, url, title = await get_ad_config()
        if enabled and not url:
            url = DEFAULT_CHANNEL_URL
            await set_setting("ad_url", url)
        if enabled and not title:
            title = DEFAULT_CHANNEL_TITLE
            await set_setting("ad_title", title)
        invalidate_ad_cache()
        enabled, url, title = await get_ad_config()
        update_promo_snapshot(bool(enabled), url or DEFAULT_CHANNEL_URL, title or DEFAULT_CHANNEL_TITLE)
        print(f"[ads] enabled={enabled} url={url!r} title={title!r}")
    except Exception as e:
        print(f"[ads] set_ad_enabled snapshot error: {e}")


async def set_ad_url(url: str) -> None:
    await set_setting("ad_url", (url or "").strip())
    invalidate_ad_cache()
    try:
        from utils.ui_helpers import update_promo_snapshot, refresh_promo_from_db
        await refresh_promo_from_db()
    except Exception:
        pass


async def set_ad_title(title: str) -> None:
    await set_setting("ad_title", (title or "").strip()[:64])
    invalidate_ad_cache()
    try:
        from utils.ui_helpers import refresh_promo_from_db
        await refresh_promo_from_db()
    except Exception:
        pass


def normalize_bale_url(text: str) -> str | None:
    """Extract/normalize ble.ir link like MEGA."""
    t = (text or "").strip()
    if not t:
        return None
    t = t.replace("https://", "").replace("http://", "").strip()
    if t.startswith("ble.ir/"):
        return "https://" + t
    if "ble.ir/" in t:
        idx = t.find("ble.ir/")
        return "https://" + t[idx:].split()[0]
    if t.startswith("@"):
        return f"https://ble.ir/{t[1:]}"
    # bare username
    if t.isalnum() or "_" in t:
        return f"https://ble.ir/{t}"
    return None


async def ads_home_text() -> str:
    enabled, url, title = await get_ad_config()
    status = "🟢 فعال" if enabled and url and title else "🔴 غیرفعال"
    return (
        "📢 **مدیریت دکمه تبلیغ**\n"
        "━━━━━━━━━━━━━━\n"
        f"وضعیت: {status}\n"
        f"عنوان: `{title or '—'}`\n"
        f"لینک: `{url or '—'}`\n\n"
        "با فعال‌بودن، دکمه زیر پیام‌های ربات نمایش داده می‌شود."
    )


async def ads_home_kb() -> InlineKeyboardMarkup:
    enabled, url, title = await get_ad_config()
    rows = []
    if enabled and url and title:
        rows.append([("🔴 خاموش کردن", "owner:ad:off")])
        rows.append([("✏️ لینک", "owner:ad:set_url"), ("✏️ عنوان", "owner:ad:set_title")])
    else:
        rows.append([("🟢 فعال‌سازی / تنظیم", "owner:ad:setup")])
        if url and title and not enabled:
            rows.append([("🟢 روشن کردن", "owner:ad:on")])
    rows.append([("🔙 تنظیمات", "owner:settings_hub")])
    return _kb(rows)


def ads_cancel_kb() -> InlineKeyboardMarkup:
    return _kb([[("↩️ لغو", "owner:ads"), ("🔙 Owner", "owner:home")]])
