# ==========================================
# Max 7 visible buttons per private screen
# ==========================================

from bale import InlineKeyboardMarkup, InlineKeyboardButton
from contextvars import ContextVar

_panel_owner: ContextVar = ContextVar("panel_owner", default=None)


def set_panel_owner(user_id):
    return _panel_owner.set(int(user_id) if user_id is not None else None)


def reset_panel_owner(token):
    try:
        _panel_owner.reset(token)
    except Exception:
        pass


def get_panel_owner():
    return _panel_owner.get()


def glass(*rows, owner_id=None) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد شیشه‌ای سازگار با Bale.
    اگر owner_id داده شود، callbackها قفل می‌شوند برای همان کاربر (در گروه).
    """
    from utils.panel_lock import tag_data
    if owner_id is None:
        owner_id = get_panel_owner()
    kb = InlineKeyboardMarkup()
    row_num = 1
    for row in rows:
        if not row:
            continue
        if (
            isinstance(row, tuple)
            and len(row) == 2
            and isinstance(row[0], str)
            and isinstance(row[1], str)
        ):
            items = [row]
        elif isinstance(row, (list, tuple)):
            items = list(row)
        else:
            continue
        for item in items:
            if not isinstance(item, (list, tuple)) or len(item) < 2:
                continue
            text, data = item[0], item[1]
            if not isinstance(text, str) or not isinstance(data, str):
                continue
            if owner_id is not None:
                data = tag_data(data, owner_id)
            kb.add(
                InlineKeyboardButton(text=text, callback_data=data),
                row=row_num,
            )
        row_num += 1
    return kb


def glass_url(*rows) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    row_num = 1
    for row in rows:
        if not row:
            continue
        if (
            isinstance(row, tuple)
            and len(row) == 2
            and isinstance(row[0], str)
            and isinstance(row[1], str)
        ):
            items = [row]
        else:
            items = list(row)
        for item in items:
            if not isinstance(item, (list, tuple)) or len(item) < 2:
                continue
            text, url = item[0], item[1]
            kb.add(
                InlineKeyboardButton(text=text, url=url),
                row=row_num,
            )
        row_num += 1
    return kb


def _count_buttons(kb) -> int:
    """شمارش دکمه برای تست."""
    try:
        total = 0
        for row in getattr(kb, "inline_keyboard", None) or []:
            total += len(row)
        return total
    except Exception:
        return -1


# ---------- Main Menu (≤6 buttons) ----------
def main_menu_kb():
    """منوی اصلی Meowixi — فشرده و بدون Halloween."""
    return glass(
        [("👤 پروفایل", "menu:profile"), ("🐈 گربه من", "pet:home")],
        [("🎮 بازی‌ها", "menu:play"), ("🎁 روزانه", "menu:daily")],
        [("🛒 فروشگاه", "shop:home"), ("📜 راهنما", "menu:help")],
    )

def back_main_kb():
    return glass(
        [("🏠 منوی اصلی", "menu:main")],
    )


def help_kb():
    return glass(
        [("📖 راهنما", "menu:guide"), ("ℹ️ درباره", "menu:about")],
        [("🎁 روزانه", "menu:daily"), ("🐛 گزارش", "menu:report")],
        [("🐱 گپ میو", "menu:global_group")],
        [("🏠 منوی اصلی", "menu:main")],
    )


def play_hub_kb():
    """هاب بازی و اقتصاد — ۶ دکمه + بازگشت."""
    return glass(
        [("⚔️ نبرد", "battle:home"), ("🎮 مینی‌گیم", "games:home")],
        [("🏦 بانک", "bank:home"), ("🏆 رنکینگ", "menu:rank")],
        [("🎯 مأموریت", "menu:missions"), ("🏅 دستاورد", "menu:achieve")],
        [("🏠 منوی اصلی", "menu:main")],
    )


def profile_kb():
    rows = [
        [("🔄 بروزرسانی", "menu:profile"), ("🐈 گربه من", "pet:home")],
        [("🏦 بانک", "bank:home"), ("🏆 رنکینگ", "menu:rank")],
        [("🏠 منوی اصلی", "menu:main")],
    ]
    return glass(*rows)


# ---------- Pet (≤7) ----------
def pet_home_kb(has_pet=True, awaiting=False):
    if awaiting:
        return glass(
            [("✏️ نام را در چت بفرست", "pet:await_hint")],
            [("🏠 منوی اصلی", "menu:main")],
        )
    if not has_pet:
        return glass(
            [("✨ ساخت گربه جدید", "pet:create")],
            [("🏠 منوی اصلی", "menu:main")],
        )
    # ≤7 دکمه: غذا/بازی/خواب/حموم/وضعیت/بیشتر/منو
    return glass(
        [("🍖 غذا", "pet:feed"), ("🎾 بازی", "pet:play_menu")],
        [("💤 خواب", "pet:sleep"), ("🧼 شستن", "pet:bath")],
        [("📊 وضعیت", "pet:status"), ("⚙️ بیشتر", "pet:more")],
        [("🏠 منوی اصلی", "menu:main")],
    )


def pet_more_kb():
    return glass(
        [("🫶 نوازش", "pet:pet"), ("🎁 هدیه", "pet:gift")],
        [("🔧 تعمیر تخت", "pet:repair_bed"), ("⬆️ ارتقا", "pet:levelup")],
        [("✏️ تغییر نام", "pet:rename")],
        [("🔙 برگشت", "pet:home")],
    )


def pet_play_kb():
    return glass(
        [("🎾 توپ", "pet:play:ball"), ("🧶 نخ", "pet:play:yarn")],
        [("🔴 لیزر", "pet:play:laser")],
        [("🔙 برگشت", "pet:home")],
    )


# ---------- Battle ----------
def battle_home_kb():
    return glass(
        [("⚔️ ورود به صف", "battle:queue"), ("🚪 خروج از صف", "battle:leave_queue")],
        [("🏋️ باشگاه", "battle:gym"), ("📊 آمار", "battle:home")],
        [("🎮 بازی‌ها", "menu:play")],
        [("🏠 منوی اصلی", "menu:main")],
    )


def gym_kb():
    return glass(
        [("⬆️ ارتقا باشگاه", "battle:gym_up")],
        [("⚔️ نبرد", "battle:home")],
        [("🏠 منوی اصلی", "menu:main")],
    )


# ---------- Bank ----------
def bank_home_kb(has_bank=True):
    if not has_bank:
        return glass(
            [("💳 افتتاح حساب", "bank:open")],
            [("🏠 منوی اصلی", "menu:main")],
        )
    return glass(
        [("📥 واریز", "bank:deposit"), ("📤 برداشت", "bank:withdraw")],
        [("💸 انتقال", "bank:transfer"), ("💳 کارت", "bank:card")],
        [("🏠 منوی اصلی", "menu:main")],
    )


def bank_cancel_kb():
    return glass(
        [("❌ لغو", "bank:home")],
        [("🏠 منوی اصلی", "menu:main")],
    )


# ---------- Shop (category + ≤5 items per page) ----------
def shop_kb(items, category: str | None = None, page: int = 0):
    """حداکثر ۵ آیتم + ناوبری ≤۷ دکمه."""
    filtered = list(items or [])
    if category:
        filtered = [i for i in filtered if (i.get("item_type") or "") == category]
    page_size = 5
    start = page * page_size
    chunk = filtered[start: start + page_size]
    rows = []
    for it in chunk:
        name = it.get("name") or it.get("item_id") or "?"
        price = it.get("price", 0)
        item_id = it.get("item_id") or "x"
        # کوتاه‌کردن برچسب
        label = f"{name} · {price}🪙"
        if len(label) > 28:
            label = label[:26] + "…"
        rows.append([(label, f"shop:buy:{item_id}")])
    nav = []
    if start > 0:
        nav.append(("◀️", f"shop:page:{category or 'all'}:{page - 1}"))
    if start + page_size < len(filtered):
        nav.append(("▶️", f"shop:page:{category or 'all'}:{page + 1}"))
    if nav:
        rows.append(nav)
    rows.append([("📂 دسته‌ها", "shop:cats"), ("🎒 کیف", "shop:inv")])
    rows.append([("🏠 منوی اصلی", "menu:main")])
    # برش سخت ≤۷
    flat = []
    for r in rows:
        flat.extend(r)
    if len(flat) > 7:
        # اولویت: آیتم‌ها + منوی اصلی
        rows = rows[:5]
        rows.append([("🏠 منوی اصلی", "menu:main")])
    return glass(*rows)


def shop_cats_kb():
    return glass(
        [("🥣 غذا", "shop:cat:food"), ("🎾 اسباب‌بازی", "shop:cat:toy")],
        [("🛏 جای‌خواب", "shop:cat:bed"), ("🎁 هدیه", "shop:cat:gift")],
        [("🛒 همه", "shop:home")],
        [("🏠 منوی اصلی", "menu:main")],
    )


# ---------- Games ----------
def games_kb():
    return glass(
        [("🎲 حدس عدد", "games:guess"), ("❓ کوییز", "games:quiz")],
        [("🐱 کوییز گربه", "games:catquiz"), ("⚡ ری‌اکشن", "games:reaction")],
        [("🎮 بازی‌ها", "menu:play")],
        [("🏠 منوی اصلی", "menu:main")],
    )


# ---------- Ranking ----------
def rank_kb():
    return glass(
        [("🐾 امتیاز", "rank:points"), ("🪙 سکه", "rank:coins")],
        [("⚔️ برد", "rank:wins"), ("🏋️ باشگاه", "rank:gym")],
        [("🏠 منوی اصلی", "menu:main")],
    )


# ---------- Owner compact ----------
def owner_nav_kb():
    return glass(
        [("📊 وضعیت", "owner:status"), ("👥 مدیریت", "owner:mgmt")],
        [("🎁 اقتصاد", "owner:economy"), ("⚙️ تنظیمات", "owner:settings_hub")],
        [("🔙 بستن", "owner:close")],
    )
