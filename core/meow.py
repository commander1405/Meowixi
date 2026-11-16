# ==========================================
# Meowixi — Meow System (Async + Anti-Repetition)
# ==========================================

import random
import re
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from config import MEOW_COOLDOWN


async def _meow_cooldown_sec() -> float:
    try:
        from database.settings import get_setting
        raw = await get_setting("meow_cooldown_sec", None)
        if raw is not None and str(raw).strip() != "":
            return float(max(0, int(str(raw).strip())))
    except Exception:
        pass
    return float(MEOW_COOLDOWN)
from database.users import (
    create_user, get_user, update_user, increment_daily_meow,
    add_meow_points, set_last_meow, get_last_meow, get_meow_points,
)
from database.content import pick_unseen_index

TEHRAN = ZoneInfo("Asia/Tehran")

MEOW_WORDS = {
    "میو", "معو", "ماو", "میومیو", "میو میو", "میو‌میو",
    "میــــو", "میــــــو", "میاو", "میاوو", "mew", "meow",
}

MEOW_RESPONSES = [
    "🐱 میو! {name}\n✨ +{gained} امتیاز\n🐾 امتیاز فصل: {total}",
    "🌸 آفرین {name}!\n+{gained} امتیاز میو\n📊 جمع: {total}",
    "✨ میو میو~\n👤 {name}\n⭐ +{gained}\n🐾 {total}",
    "🐈 پیشی تأیید کرد!\n{name} · +{gained}\nجمع فصل: {total}",
    "🎀 میوی نرم و بامزه\n{name}\n+{gained} ⭐ · {total}",
    "🩷 دلت گرم شد از این میو\n{name}: +{gained}\n{total}",
    "🌟 امتیاز جدید!\n{name} +{gained}\n🐾 فصل: {total}",
    "🐱 میو با عشق\n{name}\n✨ +{gained} | 📊 {total}",
    "🍃 یه میوی آروم\n{name} · +{gained}\nجمع: {total}",
    "😸 Meow!\n{name} +{gained}\n🐾 {total}",
    "💫 امتیاز ثبت شد\n{name}: +{gained}\nفصل: {total}",
    "🐾 میو رسید\n{name} · +{gained} ⭐ · {total}",
]


def normalize_text(text) -> str:
    if not text:
        return ""
    t = str(text).strip().lower()
    t = t.replace("ي", "ی").replace("ك", "ک")
    t = re.sub(r"\s+", " ", t)
    return t


def is_meow(text) -> bool:
    normalized = normalize_text(text)
    if normalized in MEOW_WORDS:
        return True
    if re.fullmatch(r"می[ـ\-]*و+", normalized):
        return True
    if normalized in ("mew", "meow"):
        return True
    return False


def is_allowed_group(chat_id, chat_username):
    return chat_id is not None


def format_cooldown(seconds: float) -> str:
    seconds = max(0, int(seconds))
    m, s = divmod(seconds, 60)
    if m > 0:
        return f"{m} دقیقه و {s} ثانیه"
    return f"{s} ثانیه"


async def register_meow(user_id: int, first_name: str = "", username: str = "", chat_id=None):
    now = time.time()
    user = await get_user(user_id)
    if not user:
        await create_user(user_id, first_name=first_name, username=username, chat_id=chat_id)
        user = await get_user(user_id)

    points = random.randint(1, 20)
    coins = random.randint(1, 5)
    event_note = ""
    try:
        from database.events import apply_xp_bonus
        points, _mult, event_note = await apply_xp_bonus(points)
    except Exception:
        pass
    points = max(1, int(points))
    coins = max(1, int(coins))

    from database.users import try_claim_meow_atomic
    ok, total, remaining, coins_bal = await try_claim_meow_atomic(
        int(user_id), now, float(await _meow_cooldown_sec()), int(points), int(coins)
    )
    if not ok:
        msgs = [
            f"⏳ آروم باش، {format_cooldown(remaining)} تا میوی بعدی\n🐾 امتیاز فصل: {total}",
            f"🐱 کمی صبر کن… {format_cooldown(remaining)}\n📊 امتیاز فصل: {total}",
            f"⏰ هنوز زوده: {format_cooldown(remaining)}\n🐾 {total}",
            f"⏳ Cooldown: {format_cooldown(remaining)}\n📊 امتیاز فصل: {total}",
        ]
        return False, random.choice(msgs), 0

    if chat_id is not None:
        try:
            from database.group_stats import add_group_points
            await add_group_points(user_id, chat_id, points)
        except Exception:
            pass

    day = datetime.now(TEHRAN).strftime("%Y-%m-%d")
    try:
        await increment_daily_meow(user_id, points, day)
    except Exception:
        pass

    idx = await pick_unseen_index(user_id, "meow_response", len(MEOW_RESPONSES))
    name = first_name or (user.get("first_name") if user else None) or "پیشی"
    msg = MEOW_RESPONSES[idx].format(name=name, gained=points, total=total)
    msg += f"\n🪙 میوکوین: +{coins} (موجودی: `{coins_bal}`)"
    if event_note:
        msg += f"\n{event_note}"

    try:
        from database.missions import update_mission_progress
        from database.achievements import update_achievement_progress
        u = await get_user(user_id)
        total_meows = int(u.get("total_meows") or 0) if u else 0
        await update_mission_progress(user_id, "meows", 1)
        await update_achievement_progress(user_id, "meows", total_meows)
    except Exception:
        pass

    return True, msg, points
