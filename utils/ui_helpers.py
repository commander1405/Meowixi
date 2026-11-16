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

_message_patched = False

# sync snapshot for with_promo (refreshed by async load)
_promo_snapshot = {
    "enabled": False,
    "url": "",
    "title": "",
}


def update_promo_snapshot(enabled: bool, url: str, title: str, studio_on: bool = False) -> None:
    _promo_snapshot["enabled"] = bool(enabled)
    _promo_snapshot["url"] = (url or "").strip()
    _promo_snapshot["title"] = (title or "").strip() or DEFAULT_CHANNEL_TITLE


async def refresh_promo_from_db() -> None:
    try:
        from admin.ads_mgmt import get_ad_config
        enabled, url, title = await get_ad_config()
        update_promo_snapshot(enabled, url, title)
    except Exception as e:
        logger.debug("refresh_promo_from_db: %s", e)


def channel_button() -> InlineKeyboardButton | None:
    if not _promo_snapshot.get("enabled"):
        return None
    url = (_promo_snapshot.get("url") or "").strip() or DEFAULT_CHANNEL_URL
    title = (_promo_snapshot.get("title") or "").strip() or DEFAULT_CHANNEL_TITLE
    if not url:
        return None
    try:
        return InlineKeyboardButton(text=str(title)[:64], url=str(url))
    except TypeError:
        # older signature variants
        try:
            return InlineKeyboardButton(str(title)[:64], url=str(url))
        except Exception as e:
            logger.error("channel_button create failed: %s", e)
            return None



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
    """دکمه تبلیغ قابل‌تنظیم مالک زیر پیام‌ها.
    فقط اگر owner تبلیغ را فعال کرده باشد.
    MenuKeyboard بدون تغییر برمی‌گردد.
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
        kb_list = getattr(markup, "keyboards", None)
        return markup if kb_list else components

    next_row = max_row + 1
    ad = channel_button()
    if ad is not None:
        u = _button_url(ad)
        if u and u not in existing_urls:
            try:
                markup.add(ad, row=next_row)
            except Exception as e:
                logger.debug("add ad btn: %s", e)

    kb_list = getattr(markup, "keyboards", None)
    if not kb_list:
        return components
    return markup


def with_studio(components=None):
    """سازگاری قدیمی — استدیو حذف شده، فقط تبلیغ مالک."""
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



async def reply_text(message, text, components=None, *, ad: bool = True, **kwargs):
    """ارسال قطعی با دکمه تبلیغ اینلاین وقتی ad=True و تبلیغ فعال است.
    به پچ Message.reply وابسته نیست.
    """
    text = str(text if text is not None else "…")
    is_menu = components is not None and type(components).__name__ in (
        "MenuKeyboardMarkup", "ReplyKeyboardMarkup"
    )
    if is_menu:
        kb = components
    elif ad:
        # refresh soft from snapshot; caller may await refresh_promo_from_db first
        kb = with_promo(components)
    else:
        kb = components

    reply = getattr(message, "reply", None)
    if not callable(reply):
        raise RuntimeError("message.reply missing")

    # try several call signatures used by different bale versions
    attempts = []
    if kb is not None:
        attempts.extend([
            lambda: reply(text, components=kb),
            lambda: reply(text, components=kb, **kwargs) if kwargs else None,
            lambda: reply(content=text, components=kb),
        ])
    attempts.extend([
        lambda: reply(text),
        lambda: reply(content=text),
    ])
    last_err = None
    for fn in attempts:
        if fn is None:
            continue
        try:
            return await fn()
        except TypeError as e:
            last_err = e
            continue
        except Exception as e:
            last_err = e
            continue
    if last_err:
        raise last_err
    return None


def build_ad_keyboard():
    """فقط ردیف دکمه تبلیغ (و استدیو در صورت فعال بودن)."""
    return with_promo(None)



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
