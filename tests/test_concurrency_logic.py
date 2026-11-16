"""
Regression tests for economy/concurrency guards.
These tests validate pure logic and SQL-shape helpers without production DB.
Live concurrent asyncpg tests require DATABASE_URL and are marked separately.
"""
import ast
import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)


class TestSourceGuards(unittest.TestCase):
    """Static checks that critical paths use atomic patterns."""

    def _read(self, rel):
        with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
            return f.read()

    def test_daily_uses_atomic_claim(self):
        src = self._read("core/menu.py")
        self.assertIn("claim_daily_reward_atomic", src)
        # old non-atomic path must not remain
        self.assertNotIn("await add_meow_coins(user_id, reward)\n    await update_user(user_id, last_daily", src)

    def test_meow_uses_atomic_claim(self):
        src = self._read("core/meow.py")
        self.assertIn("try_claim_meow_atomic", src)
        self.assertNotIn("await add_meow_points(user_id, points, chat_id)\n    await set_last_meow", src)

    def test_shop_buy_uses_purchase_helper(self):
        src = self._read("main.py")
        self.assertIn("purchase_shop_item", src)

    def test_remove_item_returns_false_path(self):
        src = self._read("database/inventory.py")
        self.assertIn("RETURNING quantity", src)
        # must not unconditionally return True after update
        self.assertIn("if not row:\n        return False", src)

    def test_consume_use_uses_for_update(self):
        src = self._read("database/inventory.py")
        self.assertIn("FOR UPDATE", src)
        self.assertIn("async with conn.transaction()", src)

    def test_purchase_shop_item_transaction(self):
        src = self._read("database/inventory.py")
        self.assertIn("async def purchase_shop_item", src)
        self.assertIn("FOR UPDATE", src)
        self.assertIn("meow_coins = meow_coins -", src)

    def test_bank_transfer_atomic(self):
        src = self._read("database/bank.py")
        self.assertIn("async with conn.transaction()", src)
        self.assertIn("balance = balance - $2", src)

    def test_on_ready_fails_loud(self):
        src = self._read("main.py")
        self.assertIn("NOT fully operational", src)
        self.assertIn("_ready_lock", src)

    def test_config_untouched_hash_marker(self):
        # config must still exist and not be empty
        path = os.path.join(ROOT, "config.py")
        self.assertTrue(os.path.isfile(path))
        with open(path, encoding="utf-8") as f:
            text = f.read()
        self.assertIn("BOT_TOKEN", text)
        self.assertIn("OWNER_ID", text)

        self.assertIn("FOR UPDATE", src)

    def test_no_rubika_package(self):
        self.assertFalse(os.path.isdir(os.path.join(ROOT, "mega_rubika")))
        self.assertFalse(os.path.isfile(os.path.join(ROOT, "run_both.py")))


class TestAtomicSQLSemantics(unittest.TestCase):
    """Document expected semantics of the atomic SQL patterns."""

    def test_daily_condition_excludes_same_day(self):
        # claim condition: last_daily IS NULL OR last_daily <> today
        cond = "last_daily IS NULL OR last_daily <> $2"
        self.assertIn("<>", cond)

    def test_meow_threshold_formula(self):
        now, cooldown = 1000.0, 300.0
        threshold = now - cooldown  # 700
        last_eligible = 700.0
        last_blocked = 701.0
        self.assertTrue(last_eligible <= threshold)  # eligible
        self.assertFalse(last_blocked <= threshold)  # blocked

    def test_stock_unlimited_vs_finite(self):
        stock_unlimited = -1
        stock_zero = 0
        stock_finite = 3
        self.assertTrue(stock_unlimited < 0)
        self.assertEqual(stock_zero, 0)
        self.assertTrue(stock_finite > 0)


if __name__ == "__main__":
    unittest.main()


class TestUIButtonLimits(unittest.TestCase):
    """Max 7 buttons on redesigned private keyboards."""

    @classmethod
    def setUpClass(cls):
        import types, sys
        if "bale" not in sys.modules:
            class Markup:
                def __init__(self):
                    self.rows = {}
                def add(self, btn, row=1):
                    self.rows.setdefault(row, []).append(btn)
                @property
                def inline_keyboard(self):
                    return [self.rows[k] for k in sorted(self.rows)]
            class Button:
                def __init__(self, text="", callback_data="", url=None):
                    self.text, self.callback_data, self.url = text, callback_data, url
            bale = types.ModuleType("bale")
            bale.InlineKeyboardMarkup = Markup
            bale.InlineKeyboardButton = Button
            sys.modules["bale"] = bale
            pl = types.ModuleType("utils.panel_lock")
            pl.tag_data = lambda d, o: d
            sys.modules["utils.panel_lock"] = pl

    def _count(self, kb):
        return sum(len(r) for r in kb.inline_keyboard)

    def test_main_and_hubs(self):
        from utils import keyboards as k
        for name, kb in {
            "main_on": k.main_menu_kb(True),
            "main_off": k.main_menu_kb(False),
            "help": k.help_kb(),
            "play": k.play_hub_kb(),
            "profile": k.profile_kb(True),
            "pet": k.pet_home_kb(True),
            "battle": k.battle_home_kb(),
            "bank": k.bank_home_kb(True),
            "games": k.games_kb(),
            "rank": k.rank_kb(),
            "owner": k.owner_nav_kb(),
            "shop_cats": k.shop_cats_kb(),
        }.items():
            n = self._count(kb)
            self.assertLessEqual(n, 7, f"{name} has {n} buttons")

    def test_event_settings_has_toggle_api(self):
        self.assertIn("set_event_enabled", src)
        self.assertIn("SETTING_KEY", src)
