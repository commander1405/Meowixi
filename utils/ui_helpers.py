# ==========================================
# Meowixi — UI Helpers (Configurable ad + Studio)
# پورت منطق دکمه تبلیغ MEGA + دکمه استدیو اختیاری
# ==========================================

from __future__ import annotations

import logging
from typing import Optional

from bale import InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger("meowbot.ui")

# fallback سخت‌کد اگر DB خالی باشد (رفتار قبلی)
DEFAULT_CHANNEL_URL = "https://ble.ir/join/AGwTW3RLb3"
DEFAULT_CHANNEL_TITLE = "عضویت در کانال"
STUDIO_BUTTON_TEXT = "🌑 دارک نایت استدیو"
STUDIO_BUTTON_URL = "https://ble.ir/join/FetpvYjpGQ"

_message_patched = False

# sync snapshot for with_promo (refreshed by async load)
_promo_snapshot = {
    "enabled": False,
    "url": "",
    "title": "",
    "studio_on": True,
}


def update_promo_snapshot(enabled: bool, url: str, title: str, studio_on: bool = True) -> None:
    _promo_snapshot["enabled"] = bool(enabled)
    _promo_snapshot["url"] = (url or "").strip()
    _promo_snapshot["title"] = (title or "").strip() or DEFAULT_CHANNEL_TITLE
    _promo_snapshot["studio_on"] = bool(studio_on)


async def refresh_promo_from_db() -> None:
    try:
        from admin.ads_mgmt import get_ad_config
        enabled, url, title = await get_ad_config()
        from database.settings import get_setting
        studio_raw = await get_setting("studio_button_enabled", "1")
        studio_on = str(studio_raw or "1").strip().lower() in ("1", "true", "yes", "on")
        update_promo_snapshot(enabled, url, title, studio_on)
    except Exception as e:
        logger.debug("refresh_promo_from_db: %s", e)


def channel_button() -> InlineKeyboardButton | None:
    if not _promo_snapshot.get("enabled"):
        return None
    url = _promo_snapshot.get("url") or ""
    title = _promo_snapshot.get("title") or DEFAULT_CHANNEL_TITLE
    if not url:
        return None
    return InlineKeyboardButton(text=title[:64], url=url)


def studio_button() -> InlineKeyboardButton:
    return InlineKeyboardButton(text=STUDIO_BUTTON_TEXT, url=STUDIO_BUTTON_URL)


def _iter_keyboard_items(components) -> list:
    out = []
    if components is None:
        return out
    keyboards = getattr(components, "keyboards", None)
    if not keyboards:
        return out
    for item in keyboards:
        btn = getattr(item, "item", item)
        row = getattr(item, "row", None) or 1
        try:
            row = int(row)
        except (TypeError, ValueError):
            row = 1
        out.append((btn, row))
    return out


def _button_url(btn) -> Optional[str]:
    if btn is None:
        return None
    u = getattr(btn, "url", None)
    if u:
        return str(u)
    to_dict = getattr(btn, "to_dict", None)
    if callable(to_dict):
        try:
            d = to_dict()
            if isinstance(d, dict) and d.get("url"):
                return str(d["url"])
        except Exception:
            pass
    return None



def with_promo(components=None, *, skip_ad: bool = False):
    """همیشه دکمه تبلیغ فعال را زیر پیام اینلاین بچسبان.
    MenuKeyboard جداست و با اینلاین قاطی نمی‌شود؛ در آن حالت همان MenuKeyboard برمی‌گردد
    و تبلیغ روی پیام‌های بدون MenuKeyboard (مثل میو) قطعی می‌آید.
    """
    if components is not None and type(components).__name__ in ("MenuKeyboardMarkup", "ReplyKeyboardMarkup"):
        return components

    markup = InlineKeyboardMarkup()
    max_row = 0
    existing_urls = set()

    for btn, row in _iter_keyboard_items(components):
        if row > max_row:
            max_row = row
        u = _button_url(btn)
        if u:
            existing_urls.add(u)
        try:
            markup.add(btn, row=row)
        except Exception:
            pass

    if skip_ad:
        return markup if max_row > 0 else components

    next_row = max_row + 1
    ad = channel_button()
    if ad is not None:
        u = _button_url(ad)
        if u and u not in existing_urls:
            try:
                markup.add(ad, row=next_row)
                next_row += 1
                existing_urls.add(u)
            except Exception as e:
                logger.debug("add ad btn: %s", e)

    # استدیو اختیاری
    if _promo_snapshot.get("studio_on", True):
        if STUDIO_BUTTON_URL not in existing_urls:
            try:
                markup.add(studio_button(), row=next_row)
            except Exception:
                pass

    # اگر هیچ دکمه‌ای نبود و تبلیغ هم نبود
    if not getattr(markup, "keyboards", None):
        return components
    return markup



def with_studio(components=None):
    return with_promo(components)


async def send_message(bot, chat_id, text, components=None, **kwargs):
    components = with_promo(components)
    return await bot.send_message(chat_id, text, components=components, **kwargs)


def _patch_bot_instance(bot) -> None:
    for attr in (
        "send_message",
        "send_photo",
        "send_document",
        "send_video",
        "send_animation",
        "send_audio",
    ):
        if not hasattr(bot, attr):
            continue
        orig = getattr(bot, attr)
        if getattr(orig, "_meow_promo_patched", False):
            continue

        async def wrapped(*args, _orig=orig, **kwargs):
            if kwargs.get("skip_ad"):
                kwargs.pop("skip_ad", None)
                return await _orig(*args, **kwargs)
            if "components" in kwargs:
                kwargs["components"] = with_promo(kwargs.get("components"))
                return await _orig(*args, **kwargs)
            try:
                return await _orig(*args, components=with_promo(None), **kwargs)
            except TypeError:
                return await _orig(*args, **kwargs)

        try:
            wrapped._meow_promo_patched = True  # type: ignore
            setattr(bot, attr, wrapped)
        except Exception as e:
            print(f"⚠️ Could not patch bot.{attr}: {e}")


def patch_bot_messaging(bot=None):
    """پچ Message.reply/edit و bot.send_* برای دکمه تبلیغ زیر پیام‌ها."""
    global _message_patched
    if _message_patched:
        if bot is not None:
            _patch_bot_instance(bot)
        return

    try:
        from bale import Message
    except ImportError:
        print("⚠️ ui_helpers: bale.Message not available")
        return

    if not getattr(Message.reply, "_meow_promo_patched", False):
        _orig_reply = Message.reply

        async def reply_patched(self, *args, **kwargs):
            if kwargs.get("skip_ad"):
                kwargs.pop("skip_ad", None)
                return await _orig_reply(self, *args, **kwargs)
            if "components" in kwargs:
                kwargs["components"] = with_promo(kwargs.get("components"))
            elif len(args) >= 2:
                # reply(text, components)
                pass
            try:
                if "components" not in kwargs:
                    kwargs["components"] = with_promo(None)
                return await _orig_reply(self, *args, **kwargs)
            except TypeError:
                return await _orig_reply(self, *args, **kwargs)

        reply_patched._meow_promo_patched = True  # type: ignore
        Message.reply = reply_patched

    for method_name in ("edit_text", "edit"):
        if not hasattr(Message, method_name):
            continue
        orig = getattr(Message, method_name)
        if getattr(orig, "_meow_promo_patched", False):
            continue

        async def edit_patched(self, *args, _orig=orig, **kwargs):
            if kwargs.get("skip_ad"):
                kwargs.pop("skip_ad", None)
                return await _orig(self, *args, **kwargs)
            if "components" in kwargs and kwargs["components"] is not None:
                kwargs["components"] = with_promo(kwargs.get("components"))
            return await _orig(self, *args, **kwargs)

        try:
            edit_patched._meow_promo_patched = True  # type: ignore
            setattr(Message, method_name, edit_patched)
        except Exception:
            pass

    _message_patched = True
    if bot is not None:
        _patch_bot_instance(bot)
