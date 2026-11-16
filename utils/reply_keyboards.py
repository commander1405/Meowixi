# ==========================================
# Reply (Menu) keyboards — under user input, not under bot messages
# ==========================================
from __future__ import annotations

try:
    from bale import MenuKeyboardMarkup, MenuKeyboardButton
except Exception:  # pragma: no cover
    MenuKeyboardMarkup = None
    MenuKeyboardButton = None

# Button labels (exact match in on_message)
BTN_PROFILE = "👤 پروفایل"
BTN_PET = "🐈 گربه من"
BTN_PLAY = "🎮 بازی‌ها"
BTN_DAILY = "🎁 روزانه"
BTN_SHOP = "🛒 فروشگاه"
BTN_HELP = "📜 راهنما"
BTN_HOME = "🏠 منوی اصلی"
BTN_RANK = "🏆 رنکینگ"
BTN_BANK = "🏦 بانک"
BTN_BATTLE = "⚔️ نبرد"
BTN_GAMES = "🎯 مینی‌گیم"
BTN_MISSIONS = "🎯 مأموریت"
BTN_ACHIEVE = "🏅 دستاورد"
BTN_BACK = "◀️ بازگشت"


def _kb(rows: list[list[str]]):
    if MenuKeyboardMarkup is None:
        return None
    markup = MenuKeyboardMarkup()
    for ri, row in enumerate(rows, start=1):
        for label in row:
            markup.add(MenuKeyboardButton(text=str(label)[:64]), row=ri)
    return markup


def main_reply_kb():
    return _kb([
        [BTN_PROFILE, BTN_PET],
        [BTN_PLAY, BTN_DAILY],
        [BTN_SHOP, BTN_HELP],
    ])


def play_reply_kb():
    return _kb([
        [BTN_BATTLE, BTN_GAMES],
        [BTN_BANK, BTN_RANK],
        [BTN_MISSIONS, BTN_ACHIEVE],
        [BTN_HOME],
    ])


def pet_reply_kb():
    return _kb([
        ["🍖 غذا", "🎾 بازی"],
        ["💤 خواب", "🧼 شستن"],
        ["📊 وضعیت", "⚙️ بیشتر"],
        [BTN_HOME],
    ])


def back_home_reply_kb():
    return _kb([[BTN_HOME]])
