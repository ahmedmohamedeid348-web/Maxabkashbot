"""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║         <tg-emoji emoji-id='4958926882994127612'>💰</tg-emoji> MEGA EARNING BOT - بوت الكسب الاحترافي الشامل           ║
║                                                                      ║
║   <tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji> ملف واحد - كل الميزات - لوحة أدمن متكاملة                     ║
║                                                                      ║
║   المميزات:                                                          ║
║   • مهام يومية + اشتراك إجباري في القنوات                          ║
║   • هدية يومية عشوائية                                              ║
║   • نظام دعوة متعدد المستويات                                       ║
║   • سحب بطرق متعددة                                                 ║
║   • نظام VIP بمكافآت مضاعفة                                        ║
║   • نقاط وشارات وإنجازات                                            ║
║   • عجلة الحظ اليومية                                               ║
║   • تحديات أسبوعية                                                  ║
║   • رموز ترويجية (Promo Codes)                                      ║
║   • لوحة متصدرين                                                    ║
║   • نظام مستويات (Level Up)                                         ║
║   • إشعارات تلقائية                                                 ║
║   • لوحة أدمن شاملة داخل التيليجرام                                ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝

التثبيت:
    pip install python-telegram-bot==20.7 aiosqlite==0.19.0

التشغيل:
    python mega_bot.py

الإعداد:
    غيّر BOT_TOKEN و ADMIN_IDS في قسم CONFIG أدناه
"""

# ═══════════════════════════════════════════════════════════════
#  IMPORTS
# ═══════════════════════════════════════════════════════════════
import asyncio
import datetime
import io
import json
import logging
import random
import string
import threading
from typing import Optional

from flask import Flask, jsonify, request
from flask_cors import CORS

import aiosqlite
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ChatMember,
)
from telegram.error import TelegramError, Forbidden
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ═══════════════════════════════════════════════════════════════
#  ██████╗ ██████╗ ███╗   ██╗███████╗██╗ ██████╗
# ██╔════╝██╔═══██╗████╗  ██║██╔════╝██║██╔════╝
# ██║     ██║   ██║██╔██╗ ██║█████╗  ██║██║  ███╗
# ██║     ██║   ██║██║╚██╗██║██╔══╝  ██║██║   ██║
# ╚██████╗╚██████╔╝██║ ╚████║██║     ██║╚██████╔╝
#  ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝     ╚═╝ ╚═════╝
# ═══════════════════════════════════════════════════════════════

# 🔑 ضع توكن البوت من @BotFather
BOT_TOKEN = "8086835374:AAEOnAyxUy3xlu1ojWGqMUuRf8pNu74WJDo"

# <tg-emoji emoji-id='5114039184507536021'>👑</tg-emoji> ضع ID حسابك على تيليجرام (ممكن تضيف أكتر من أدمن)
ADMIN_IDS = [7804343757 , 6355023208]

# 🗄️ اسم ملف قاعدة البيانات
DB_PATH = "mega_bot.db"

# 🌐 اسم البوت الظاهر للمستخدمين
BOT_NAME = "<tg-emoji emoji-id='4958926882994127612'>💰</tg-emoji> بوت الكسب الاحترافي"

# <tg-emoji emoji-id='5861568308116984245'>🚀</tg-emoji> رابط البوت (غيّره لاسم البوت بتاعك)
BOT_USERNAME = "@Free_internet_kbot"  # بدون @ مثال: cashbot2025

# <tg-emoji emoji-id='5859588916604047101'>⚙️</tg-emoji> الإعدادات الافتراضية (تتغير من لوحة الأدمن)
DEFAULT_SETTINGS = {
    "referral_reward_l1":     2.0,    # مكافأة الدعوة المستوى 1
    "referral_reward_l2":     0.5,    # مكافأة الدعوة المستوى 2
    "referral_reward_l3":     0.25,   # مكافأة الدعوة المستوى 3
    "daily_gift_min":         0.5,    # أقل هدية يومية
    "daily_gift_max":         3.0,    # أكبر هدية يومية
    "min_withdraw":           6.0,    # الحد الأدنى للسحب
    "welcome_bonus":          1.0,    # مكافأة التسجيل
    "vip_multiplier":         2.0,    # مضاعف مكافآت VIP
    "maintenance_mode":       False,  # وضع الصيانة
    "force_channels":         [],     # قنوات الاشتراك الإجباري [[id, link, name], ...]
    "wheel_prizes":           [0.5, 1.0, 1.5, 2.0, 3.0, 0.25, 5.0, 0.1],
    "wheel_max_prize":        2.0,    # أقصى جائزة تطلع من العجلة بالجنيه
    "usd_to_egp":             50.0,   # سعر الدولار بالجنيه المصري
    "weekly_challenge_reward": 10.0,  # مكافأة التحدي الأسبوعي
    "weekly_challenge_tasks":  5,     # عدد المهام للتحدي الأسبوعي
    "streak_bonus":           0.5,    # مكافأة الاتساق اليومي (كل يوم متتالي)
    "max_promo_uses":         100,    # الاستخدامات الافتراضية للكود
}

# ─────── CAPTCHA: تخزين مؤقت في الذاكرة ───────
# {user_id: {"answer": int, "referred_by": int|None, "attempts": int}}
CAPTCHA_PENDING: dict = {}

# <tg-emoji emoji-id='5440539497383087970'>🏅</tg-emoji> نظام المستويات
LEVELS = [
    {"name": "مبتدئ <tg-emoji emoji-id='5974025781880295611'>🌱</tg-emoji>",      "min_earned": 0},
    {"name": "نشيط <tg-emoji emoji-id='5931795421453097161'>⚡</tg-emoji>",       "min_earned": 10},
    {"name": "متقدم <tg-emoji emoji-id='5855190238732751076'>🔥</tg-emoji>",      "min_earned": 30},
    {"name": "خبير <tg-emoji emoji-id='5956031393623445676'>💎</tg-emoji>",       "min_earned": 75},
    {"name": "نخبة <tg-emoji emoji-id='5114039184507536021'>👑</tg-emoji>",       "min_earned": 150},
    {"name": "أسطورة <tg-emoji emoji-id='5370715282044100355'>🌟</tg-emoji>",     "min_earned": 300},
]

# <tg-emoji emoji-id='5433613063754363635'>🏆</tg-emoji> الشارات والإنجازات
ACHIEVEMENTS = {
    "first_task":     {"name": "أول مهمة <tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji>",      "desc": "أكملت مهمتك الأولى",         "reward": 0.5},
    "tasks_10":       {"name": "منجز <tg-emoji emoji-id='5764978573848877254'>🎯</tg-emoji>",           "desc": "أكملت 10 مهام",              "reward": 2.0},
    "tasks_50":       {"name": "محترف <tg-emoji emoji-id='5931795421453097161'>⚡</tg-emoji>",          "desc": "أكملت 50 مهمة",             "reward": 5.0},
    "referral_1":     {"name": "مُرشِّد <tg-emoji emoji-id='5931746304207100511'>🔗</tg-emoji>",        "desc": "دعوت أول شخص",              "reward": 1.0},
    "referral_10":    {"name": "قائد المجتمع <tg-emoji emoji-id='5012839657545663163'>👥</tg-emoji>",   "desc": "دعوت 10 أشخاص",            "reward": 5.0},
    "referral_50":    {"name": "السفير <tg-emoji emoji-id='5224450179368767019'>🌍</tg-emoji>",         "desc": "دعوت 50 شخصاً",            "reward": 15.0},
    "streak_7":       {"name": "ملتزم <tg-emoji emoji-id='5855190238732751076'>🔥</tg-emoji>",          "desc": "7 أيام متتالية",            "reward": 3.0},
    "streak_30":      {"name": "أسطورة الالتزام <tg-emoji emoji-id='5433613063754363635'>🏆</tg-emoji>","desc": "30 يوم متتالي",           "reward": 15.0},
    "withdraw_first": {"name": "أول سحب <tg-emoji emoji-id='5433983375834624526'>💸</tg-emoji>",        "desc": "سحبت أول مرة",              "reward": 0.0},
    "vip_member":     {"name": "عضو VIP <tg-emoji emoji-id='5370715282044100355'>⭐</tg-emoji>",        "desc": "انضممت لـ VIP",             "reward": 0.0},
    "wheel_jackpot":  {"name": "جاكبوت <tg-emoji emoji-id='5814263327865444782'>🎰</tg-emoji>",         "desc": "ربحت الجائزة الكبرى من العجلة","reward": 0.0},
}

# <tg-emoji emoji-id='5161427856491807309'>💳</tg-emoji> طرق السحب
WITHDRAW_METHODS = {
    "vodafone":  ("📱 فودافون كاش",   None),
    "instapay":  ("انستاباي",          "5161427856491807309"),
    "orange":    ("أورنج كاش",         "5992358531955693898"),
    "etisalat":  ("اتصالات كاش",       "5845690441088899251"),
    "we":        ("WE Pay",            "6032841519298253772"),
    "bank":      ("تحويل بنكي",        "4961202017365132001"),
}

logging.basicConfig(format="%(message)s", level=logging.CRITICAL)
log = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.CRITICAL)
logging.getLogger("telegram").setLevel(logging.CRITICAL)
logging.getLogger("apscheduler").setLevel(logging.CRITICAL)


# ═══════════════════════════════════════════════════════════════
# ██████╗  █████╗ ████████╗ █████╗ ██████╗  █████╗ ███████╗███████╗
# ██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔════╝
# ██║  ██║███████║   ██║   ███████║██████╔╝███████║███████╗█████╗
# ██║  ██║██╔══██║   ██║   ██╔══██║██╔══██╗██╔══██║╚════██║██╔══╝
# ██████╔╝██║  ██║   ██║   ██║  ██║██████╔╝██║  ██║███████║███████╗
# ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝╚══════╝╚══════╝
# ═══════════════════════════════════════════════════════════════

class DB:
    """قاعدة البيانات الكاملة"""

    def __init__(self):
        self.path = DB_PATH

    async def init(self):
        async with aiosqlite.connect(self.path) as db:
            await db.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id        INTEGER PRIMARY KEY,
                    username       TEXT    DEFAULT '',
                    full_name      TEXT    DEFAULT '',
                    balance        REAL    DEFAULT 0,
                    total_earned   REAL    DEFAULT 0,
                    total_withdrawn REAL   DEFAULT 0,
                    ref_code       TEXT    UNIQUE,
                    referred_by    INTEGER DEFAULT NULL,
                    ref_count      INTEGER DEFAULT 0,
                    ref_l2_count   INTEGER DEFAULT 0,
                    is_banned      INTEGER DEFAULT 0,
                    ban_reason     TEXT    DEFAULT '',
                    is_vip         INTEGER DEFAULT 0,
                    vip_expiry     TEXT    DEFAULT NULL,
                    level          INTEGER DEFAULT 0,
                    xp             INTEGER DEFAULT 0,
                    streak         INTEGER DEFAULT 0,
                    last_streak    TEXT    DEFAULT NULL,
                    tasks_done     INTEGER DEFAULT 0,
                    join_date      TEXT,
                    last_active    TEXT,
                    last_gift      TEXT    DEFAULT NULL,
                    last_wheel     TEXT    DEFAULT NULL,
                    wheel_count    INTEGER DEFAULT 0,
                    achievements   TEXT    DEFAULT '[]',
                    notes          TEXT    DEFAULT '',
                    language       TEXT    DEFAULT 'ar'
                );

                CREATE TABLE IF NOT EXISTS tasks (
                    task_id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    title          TEXT,
                    description    TEXT,
                    reward         REAL,
                    task_type      TEXT    DEFAULT 'subscribe',
                    channel_id     TEXT    DEFAULT '',
                    channel_link   TEXT    DEFAULT '',
                    channel_name   TEXT    DEFAULT '',
                    is_private     INTEGER DEFAULT 0,
                    invite_link    TEXT    DEFAULT '',
                    is_active      INTEGER DEFAULT 1,
                    created_at     TEXT,
                    completions    INTEGER DEFAULT 0,
                    expires_at     TEXT    DEFAULT NULL
                );

                CREATE TABLE IF NOT EXISTS completed_tasks (
                    id             INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id        INTEGER,
                    task_id        INTEGER,
                    completed_at   TEXT,
                    reward_given   REAL,
                    UNIQUE(user_id, task_id)
                );

                CREATE TABLE IF NOT EXISTS withdrawals (
                    id             INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id        INTEGER,
                    amount         REAL,
                    method         TEXT,
                    account_info   TEXT,
                    status         TEXT    DEFAULT 'pending',
                    created_at     TEXT,
                    processed_at   TEXT    DEFAULT NULL,
                    admin_note     TEXT    DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS transactions (
                    id             INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id        INTEGER,
                    amount         REAL,
                    type           TEXT,
                    description    TEXT,
                    created_at     TEXT
                );

                CREATE TABLE IF NOT EXISTS promo_codes (
                    code           TEXT    PRIMARY KEY,
                    reward         REAL,
                    max_uses       INTEGER DEFAULT 100,
                    used_count     INTEGER DEFAULT 0,
                    created_by     INTEGER,
                    created_at     TEXT,
                    expires_at     TEXT    DEFAULT NULL,
                    is_active      INTEGER DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS promo_uses (
                    id             INTEGER PRIMARY KEY AUTOINCREMENT,
                    code           TEXT,
                    user_id        INTEGER,
                    used_at        TEXT,
                    UNIQUE(code, user_id)
                );

                CREATE TABLE IF NOT EXISTS weekly_challenges (
                    id             INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id        INTEGER,
                    week_start     TEXT,
                    tasks_done     INTEGER DEFAULT 0,
                    completed      INTEGER DEFAULT 0,
                    reward_claimed INTEGER DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS settings (
                    key            TEXT    PRIMARY KEY,
                    value          TEXT
                );

                CREATE TABLE IF NOT EXISTS broadcasts (
                    id             INTEGER PRIMARY KEY AUTOINCREMENT,
                    message        TEXT,
                    sent_to        INTEGER DEFAULT 0,
                    failed         INTEGER DEFAULT 0,
                    sent_at        TEXT,
                    admin_id       INTEGER
                );
            """)
            await db.commit()

        await self._load_defaults()

    async def _load_defaults(self):
        async with aiosqlite.connect(self.path) as db:
            for k, v in DEFAULT_SETTINGS.items():
                await db.execute(
                    "INSERT OR IGNORE INTO settings (key, value) VALUES (?,?)",
                    (k, json.dumps(v))
                )
            await db.commit()

    # ──────────────────────────── SETTINGS ────────────────────────────
    async def get(self, key):
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute("SELECT value FROM settings WHERE key=?", (key,))
            row = await cur.fetchone()
            if row:
                return json.loads(row[0])
            return DEFAULT_SETTINGS.get(key)

    async def set(self, key, value):
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)",
                (key, json.dumps(value))
            )
            await db.commit()

    async def all_settings(self):
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute("SELECT key, value FROM settings")
            rows = await cur.fetchall()
            return {r[0]: json.loads(r[1]) for r in rows}

    # ──────────────────────────── USERS ────────────────────────────
    async def get_user(self, user_id: int) -> Optional[dict]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
            row = await cur.fetchone()
            return dict(row) if row else None

    async def create_user(self, user_id, username, full_name, referred_by=None):
        bonus = await self.get("welcome_bonus")
        now = datetime.datetime.now().isoformat()
        ref_code = f"REF{user_id}"
        async with aiosqlite.connect(self.path) as db:
            await db.execute("""
                INSERT OR IGNORE INTO users
                (user_id, username, full_name, balance, total_earned, ref_code, referred_by, join_date, last_active)
                VALUES (?,?,?,?,?,?,?,?,?)
            """, (user_id, username, full_name, bonus, bonus, ref_code, referred_by, now, now))
            await db.execute("""
                INSERT OR IGNORE INTO transactions (user_id, amount, type, description, created_at)
                VALUES (?,?,'bonus','مكافأة الترحيب',?)
            """, (user_id, bonus, now))
            await db.commit()

        # مكافأة من دعاه (متعددة المستويات)
        if referred_by:
            ref_user = await self.get_user(referred_by)
            if ref_user:
                r1 = await self.get("referral_reward_l1")
                await self.add_balance(referred_by, r1, "referral", f"دعوة مباشرة - {full_name}")
                async with aiosqlite.connect(self.path) as db:
                    await db.execute("UPDATE users SET ref_count=ref_count+1 WHERE user_id=?", (referred_by,))
                    await db.commit()
                # المستوى الثاني
                if ref_user.get("referred_by"):
                    r2 = await self.get("referral_reward_l2")
                    await self.add_balance(ref_user["referred_by"], r2, "referral", f"دعوة غير مباشرة (مستوى 2) - {full_name}")
                    async with aiosqlite.connect(self.path) as db:
                        await db.execute("UPDATE users SET ref_l2_count=ref_l2_count+1 WHERE user_id=?", (ref_user["referred_by"],))
                        await db.commit()
                    # المستوى الثالث
                    ref2 = await self.get_user(ref_user["referred_by"])
                    if ref2 and ref2.get("referred_by"):
                        r3 = await self.get("referral_reward_l3")
                        await self.add_balance(ref2["referred_by"], r3, "referral", f"دعوة غير مباشرة (مستوى 3) - {full_name}")

        await self._check_achievements(user_id)

    async def get_or_create(self, user_id, username, full_name, referred_by=None):
        user = await self.get_user(user_id)
        if user:
            async with aiosqlite.connect(self.path) as db:
                await db.execute(
                    "UPDATE users SET last_active=?, username=?, full_name=? WHERE user_id=?",
                    (datetime.datetime.now().isoformat(), username or "", full_name or "", user_id)
                )
                await db.commit()
            return await self.get_user(user_id), False
        await self.create_user(user_id, username, full_name, referred_by)
        return await self.get_user(user_id), True

    async def add_balance(self, user_id, amount, trans_type="manual", desc=""):
        async with aiosqlite.connect(self.path) as db:
            if amount >= 0:
                await db.execute(
                    "UPDATE users SET balance=balance+?, total_earned=total_earned+? WHERE user_id=?",
                    (amount, amount, user_id)
                )
            else:
                await db.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (amount, user_id))
            await db.execute("""
                INSERT INTO transactions (user_id, amount, type, description, created_at)
                VALUES (?,?,?,?,?)
            """, (user_id, amount, trans_type, desc, datetime.datetime.now().isoformat()))
            await db.commit()
        await self._check_level(user_id)

    async def _check_level(self, user_id):
        user = await self.get_user(user_id)
        if not user:
            return
        earned = user["total_earned"]
        new_level = 0
        for i, lv in enumerate(LEVELS):
            if earned >= lv["min_earned"]:
                new_level = i
        if new_level != user["level"]:
            async with aiosqlite.connect(self.path) as db:
                await db.execute("UPDATE users SET level=? WHERE user_id=?", (new_level, user_id))
                await db.commit()

    async def _check_achievements(self, user_id):
        user = await self.get_user(user_id)
        if not user:
            return
        earned = json.loads(user.get("achievements") or "[]")
        new_ones = []

        checks = {
            "first_task":     user["tasks_done"] >= 1,
            "tasks_10":       user["tasks_done"] >= 10,
            "tasks_50":       user["tasks_done"] >= 50,
            "referral_1":     user["ref_count"] >= 1,
            "referral_10":    user["ref_count"] >= 10,
            "referral_50":    user["ref_count"] >= 50,
            "streak_7":       user["streak"] >= 7,
            "streak_30":      user["streak"] >= 30,
        }
        for key, cond in checks.items():
            if cond and key not in earned:
                earned.append(key)
                new_ones.append(key)
                reward = ACHIEVEMENTS[key]["reward"]
                if reward > 0:
                    await self.add_balance(user_id, reward, "achievement", ACHIEVEMENTS[key]["name"])

        if new_ones:
            async with aiosqlite.connect(self.path) as db:
                await db.execute(
                    "UPDATE users SET achievements=? WHERE user_id=?",
                    (json.dumps(earned), user_id)
                )
                await db.commit()

        return new_ones

    async def ban(self, user_id, reason=""):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("UPDATE users SET is_banned=1, ban_reason=? WHERE user_id=?", (reason, user_id))
            await db.commit()

    async def unban(self, user_id):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("UPDATE users SET is_banned=0, ban_reason='' WHERE user_id=?", (user_id,))
            await db.commit()

    async def set_vip(self, user_id, days=30):
        expiry = (datetime.datetime.now() + datetime.timedelta(days=days)).isoformat()
        async with aiosqlite.connect(self.path) as db:
            await db.execute("UPDATE users SET is_vip=1, vip_expiry=? WHERE user_id=?", (expiry, user_id))
            await db.commit()
        await self._grant_achievement(user_id, "vip_member")

    async def remove_vip(self, user_id):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("UPDATE users SET is_vip=0, vip_expiry=NULL WHERE user_id=?", (user_id,))
            await db.commit()

    async def _grant_achievement(self, user_id, key):
        user = await self.get_user(user_id)
        if not user:
            return
        earned = json.loads(user.get("achievements") or "[]")
        if key not in earned:
            earned.append(key)
            async with aiosqlite.connect(self.path) as db:
                await db.execute("UPDATE users SET achievements=? WHERE user_id=?", (json.dumps(earned), user_id))
                await db.commit()

    async def get_all_users(self, include_banned=False):
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            q = "SELECT * FROM users" + ("" if include_banned else " WHERE is_banned=0") + " ORDER BY join_date DESC"
            cur = await db.execute(q)
            return [dict(r) for r in await cur.fetchall()]

    async def get_active_users(self, days=7):
        cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT * FROM users WHERE last_active>? AND is_banned=0", (cutoff,)
            )
            return [dict(r) for r in await cur.fetchall()]

    async def get_leaderboard(self, limit=10):
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT * FROM users WHERE is_banned=0 ORDER BY total_earned DESC LIMIT ?", (limit,)
            )
            return [dict(r) for r in await cur.fetchall()]

    async def get_stats(self):
        async with aiosqlite.connect(self.path) as db:
            def q(sql, *args):
                return db.execute(sql, args)

            total   = (await (await q("SELECT COUNT(*) FROM users")).fetchone())[0]
            active  = (await (await q("SELECT COUNT(*) FROM users WHERE last_active>?",
                                      (datetime.datetime.now() - datetime.timedelta(hours=24)).isoformat()
                                      )).fetchone())[0]
            vip     = (await (await q("SELECT COUNT(*) FROM users WHERE is_vip=1")).fetchone())[0]
            banned  = (await (await q("SELECT COUNT(*) FROM users WHERE is_banned=1")).fetchone())[0]
            tasks_a = (await (await q("SELECT COUNT(*) FROM tasks WHERE is_active=1")).fetchone())[0]
            pw      = (await (await q("SELECT COUNT(*) FROM withdrawals WHERE status='pending'")).fetchone())[0]
            tw      = (await (await q("SELECT COALESCE(SUM(amount),0) FROM withdrawals WHERE status='approved'")).fetchone())[0]
            new_24  = (await (await q("SELECT COUNT(*) FROM users WHERE join_date>?",
                                      (datetime.datetime.now() - datetime.timedelta(hours=24)).isoformat()
                                      )).fetchone())[0]
            tasks_d = (await (await q("SELECT COUNT(*) FROM completed_tasks")).fetchone())[0]
            bal_sum = (await (await q("SELECT COALESCE(SUM(balance),0) FROM users")).fetchone())[0]

        return {
            "total": total, "active_24h": active, "vip": vip, "banned": banned,
            "active_tasks": tasks_a, "pending_withdrawals": pw, "total_withdrawn": tw,
            "new_24h": new_24, "tasks_done": tasks_d, "balance_sum": bal_sum,
        }

    # ──────────────────────────── TASKS ────────────────────────────
    async def add_task(self, title, desc, reward, task_type, channel_id, channel_link,
                       channel_name, is_private=False, invite_link=""):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("""
                INSERT INTO tasks (title, description, reward, task_type, channel_id, channel_link,
                                   channel_name, is_private, invite_link, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (title, desc, reward, task_type, channel_id, channel_link,
                  channel_name, 1 if is_private else 0, invite_link,
                  datetime.datetime.now().isoformat()))
            await db.commit()

    async def get_tasks(self, active_only=True):
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            q = "SELECT * FROM tasks" + (" WHERE is_active=1" if active_only else "") + " ORDER BY reward DESC"
            cur = await db.execute(q)
            return [dict(r) for r in await cur.fetchall()]

    async def get_task(self, task_id):
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,))
            r = await cur.fetchone()
            return dict(r) if r else None

    async def delete_task(self, task_id):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("DELETE FROM tasks WHERE task_id=?", (task_id,))
            await db.commit()

    async def toggle_task(self, task_id):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("UPDATE tasks SET is_active=1-is_active WHERE task_id=?", (task_id,))
            await db.commit()

    async def is_task_done(self, user_id, task_id):
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(
                "SELECT id FROM completed_tasks WHERE user_id=? AND task_id=?", (user_id, task_id)
            )
            return await cur.fetchone() is not None

    async def complete_task(self, user_id, task_id, reward):
        try:
            async with aiosqlite.connect(self.path) as db:
                await db.execute("""
                    INSERT INTO completed_tasks (user_id, task_id, completed_at, reward_given)
                    VALUES (?,?,?,?)
                """, (user_id, task_id, datetime.datetime.now().isoformat(), reward))
                await db.execute("UPDATE tasks SET completions=completions+1 WHERE task_id=?", (task_id,))
                await db.execute("UPDATE users SET tasks_done=tasks_done+1 WHERE user_id=?", (user_id,))
                await db.commit()
            await self.add_balance(user_id, reward, "task", "إكمال مهمة")
            # تحديث الاتساق اليومي (streak)
            await self._update_streak(user_id)
            # تحديث التحدي الأسبوعي
            await self._update_weekly_challenge(user_id)
            await self._check_achievements(user_id)
            return True
        except Exception:
            return False

    async def _update_streak(self, user_id):
        user = await self.get_user(user_id)
        if not user:
            return
        now = datetime.datetime.now().date()
        last = user.get("last_streak")
        new_streak = user["streak"]

        if last:
            last_date = datetime.date.fromisoformat(last)
            diff = (now - last_date).days
            if diff == 1:
                new_streak += 1
                bonus = await self.get("streak_bonus")
                await self.add_balance(user_id, bonus, "streak", f"مكافأة الاتساق - يوم {new_streak}")
            elif diff > 1:
                new_streak = 1
        else:
            new_streak = 1

        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "UPDATE users SET streak=?, last_streak=? WHERE user_id=?",
                (new_streak, now.isoformat(), user_id)
            )
            await db.commit()

    async def _update_weekly_challenge(self, user_id):
        week_start = (datetime.datetime.now() - datetime.timedelta(days=datetime.datetime.now().weekday())).date().isoformat()
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(
                "SELECT * FROM weekly_challenges WHERE user_id=? AND week_start=?", (user_id, week_start)
            )
            row = await cur.fetchone()
            if not row:
                await db.execute("""
                    INSERT INTO weekly_challenges (user_id, week_start, tasks_done)
                    VALUES (?,?,1)
                """, (user_id, week_start))
            else:
                await db.execute("""
                    UPDATE weekly_challenges SET tasks_done=tasks_done+1
                    WHERE user_id=? AND week_start=?
                """, (user_id, week_start))
            await db.commit()

            cur = await db.execute(
                "SELECT * FROM weekly_challenges WHERE user_id=? AND week_start=?", (user_id, week_start)
            )
            ch = await cur.fetchone()
            if ch:
                target = await self.get("weekly_challenge_tasks")
                if ch[3] >= target and not ch[4]:  # tasks_done >= target and not completed
                    reward = await self.get("weekly_challenge_reward")
                    await db.execute("""
                        UPDATE weekly_challenges SET completed=1, reward_claimed=1
                        WHERE user_id=? AND week_start=?
                    """, (user_id, week_start))
                    await db.commit()
                    await self.add_balance(user_id, reward, "weekly_challenge", "إنجاز التحدي الأسبوعي <tg-emoji emoji-id='5433613063754363635'>🏆</tg-emoji>")
                    return reward
        return 0

    # ──────────────────────────── DAILY GIFT ────────────────────────────
    async def claim_gift(self, user_id):
        user = await self.get_user(user_id)
        if not user:
            return 0, False, None
        now = datetime.datetime.now()
        last = user.get("last_gift")
        if last:
            last_dt = datetime.datetime.fromisoformat(last)
            if (now - last_dt).total_seconds() < 86400:
                return 0, False, last_dt + datetime.timedelta(days=1)
        g_min = await self.get("daily_gift_min")
        g_max = await self.get("daily_gift_max")
        reward = round(random.uniform(g_min, g_max), 2)
        if user.get("is_vip"):
            reward = round(reward * await self.get("vip_multiplier"), 2)
        async with aiosqlite.connect(self.path) as db:
            await db.execute("UPDATE users SET last_gift=? WHERE user_id=?", (now.isoformat(), user_id))
            await db.commit()
        await self.add_balance(user_id, reward, "gift", "الهدية اليومية")
        return reward, True, None

    # ──────────────────────────── WHEEL ────────────────────────────
    async def spin_wheel(self, user_id):
        user = await self.get_user(user_id)
        if not user:
            return 0, False, None
        now = datetime.datetime.now()
        last = user.get("last_wheel")
        if last:
            last_dt = datetime.datetime.fromisoformat(last)
            if (now - last_dt).total_seconds() < 86400:
                return 0, False, last_dt + datetime.timedelta(days=1)
        prizes = await self.get("wheel_prizes")
        prize = random.choice(prizes)
        if user.get("is_vip"):
            prize = round(prize * await self.get("vip_multiplier"), 2)
        # سقف الجائزة - مهما كانت الأرقام في الإعدادات، أقصى ما يطلع للمستخدم 2 جنيه
        max_allowed = await self.get("wheel_max_prize")
        prize = min(prize, max_allowed)
        # جاكبوت = أعلى جائزة مسموح بها
        if prize >= max_allowed:
            await self._grant_achievement(user_id, "wheel_jackpot")
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "UPDATE users SET last_wheel=?, wheel_count=wheel_count+1 WHERE user_id=?",
                (now.isoformat(), user_id)
            )
            await db.commit()
        await self.add_balance(user_id, prize, "wheel", "عجلة الحظ <tg-emoji emoji-id='5814263327865444782'>🎰</tg-emoji>")
        return prize, True, None

    # ──────────────────────────── PROMO CODES ────────────────────────────
    async def create_promo(self, code, reward, max_uses, admin_id, expires_at=None):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO promo_codes
                (code, reward, max_uses, created_by, created_at, expires_at)
                VALUES (?,?,?,?,?,?)
            """, (code.upper(), reward, max_uses, admin_id,
                  datetime.datetime.now().isoformat(), expires_at))
            await db.commit()

    async def use_promo(self, code, user_id):
        """Returns (reward, error_msg)"""
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM promo_codes WHERE code=? AND is_active=1", (code.upper(),))
            promo = await cur.fetchone()
            if not promo:
                return 0, "<tg-emoji emoji-id='4958526153955476488'>❌</tg-emoji> الكود غير صحيح أو منتهي!"
            promo = dict(promo)
            if promo["used_count"] >= promo["max_uses"]:
                return 0, "<tg-emoji emoji-id='4958526153955476488'>❌</tg-emoji> انتهت استخدامات هذا الكود!"
            if promo["expires_at"] and datetime.datetime.fromisoformat(promo["expires_at"]) < datetime.datetime.now():
                return 0, "<tg-emoji emoji-id='4958526153955476488'>❌</tg-emoji> انتهت صلاحية هذا الكود!"
            # تحقق من استخدام سابق
            cur2 = await db.execute("SELECT id FROM promo_uses WHERE code=? AND user_id=?", (code.upper(), user_id))
            if await cur2.fetchone():
                return 0, "<tg-emoji emoji-id='4958526153955476488'>❌</tg-emoji> استخدمت هذا الكود من قبل!"
            # استخدام الكود
            await db.execute("UPDATE promo_codes SET used_count=used_count+1 WHERE code=?", (code.upper(),))
            await db.execute("""
                INSERT INTO promo_uses (code, user_id, used_at) VALUES (?,?,?)
            """, (code.upper(), user_id, datetime.datetime.now().isoformat()))
            await db.commit()
        reward = promo["reward"]
        await self.add_balance(user_id, reward, "promo", f"كود ترويجي: {code.upper()}")
        return reward, None

    async def get_promos(self):
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM promo_codes ORDER BY created_at DESC")
            return [dict(r) for r in await cur.fetchall()]

    # ──────────────────────────── WITHDRAWALS ────────────────────────────
    async def create_withdrawal(self, user_id, amount, method, account):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("""
                INSERT INTO withdrawals (user_id, amount, method, account_info, created_at)
                VALUES (?,?,?,?,?)
            """, (user_id, amount, method, account, datetime.datetime.now().isoformat()))
            await db.execute(
                "UPDATE users SET balance=balance-?, total_withdrawn=total_withdrawn+? WHERE user_id=?",
                (amount, amount, user_id)
            )
            await db.commit()
        await self._grant_achievement(user_id, "withdraw_first")

    async def get_pending_withdrawals(self):
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("""
                SELECT w.*, u.username, u.full_name FROM withdrawals w
                JOIN users u ON w.user_id=u.user_id
                WHERE w.status='pending' ORDER BY w.created_at ASC
            """)
            return [dict(r) for r in await cur.fetchall()]

    async def get_withdrawal(self, w_id):
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM withdrawals WHERE id=?", (w_id,))
            r = await cur.fetchone()
            return dict(r) if r else None

    async def process_withdrawal(self, w_id, status, note=""):
        w = await self.get_withdrawal(w_id)
        async with aiosqlite.connect(self.path) as db:
            await db.execute("""
                UPDATE withdrawals SET status=?, processed_at=?, admin_note=? WHERE id=?
            """, (status, datetime.datetime.now().isoformat(), note, w_id))
            if status == "rejected" and w:
                await db.execute(
                    "UPDATE users SET balance=balance+?, total_withdrawn=total_withdrawn-? WHERE user_id=?",
                    (w["amount"], w["amount"], w["user_id"])
                )
            await db.commit()

    # ──────────────────────────── FORCE SUBSCRIBE ────────────────────────────
    async def add_force_channel(self, channel_id, channel_link, channel_name, is_private=False, invite_link=""):
        channels = await self.get("force_channels")
        channels.append({
            "id": channel_id, "link": channel_link, "name": channel_name,
            "is_private": is_private, "invite_link": invite_link
        })
        await self.set("force_channels", channels)

    async def remove_force_channel(self, channel_id):
        channels = await self.get("force_channels")
        channels = [c for c in channels if str(c["id"]) != str(channel_id)]
        await self.set("force_channels", channels)

    async def check_force_channels(self, user_id, bot) -> list:
        """Returns list of channels user is NOT subscribed to"""
        channels = await self.get("force_channels")
        not_joined = []
        for ch in channels:
            try:
                member = await bot.get_chat_member(ch["id"], user_id)
                if member.status in [ChatMember.LEFT, ChatMember.BANNED]:
                    not_joined.append(ch)
            except TelegramError:
                not_joined.append(ch)
        return not_joined


# ═══════════════════════════════════════════════════════════════
# ██╗  ██╗███████╗██╗     ██████╗ ███████╗██████╗ ███████╗
# ██║  ██║██╔════╝██║     ██╔══██╗██╔════╝██╔══██╗██╔════╝
# ███████║█████╗  ██║     ██████╔╝█████╗  ██████╔╝███████╗
# ██╔══██║██╔══╝  ██║     ██╔═══╝ ██╔══╝  ██╔══██╗╚════██║
# ██║  ██║███████╗███████╗██║     ███████╗██║  ██║███████║
# ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝     ╚══════╝╚═╝  ╚═╝╚══════╝
# ═══════════════════════════════════════════════════════════════

db = DB()

# ═══════════════════════════════════════════════════════════════
#  ███████╗██╗      █████╗ ███████╗██╗  ██╗     █████╗ ██████╗ ██╗
#  ██╔════╝██║     ██╔══██╗██╔════╝██║ ██╔╝    ██╔══██╗██╔══██╗██║
#  █████╗  ██║     ███████║███████╗█████╔╝     ███████║██████╔╝██║
#  ██╔══╝  ██║     ██╔══██║╚════██║██╔═██╗     ██╔══██║██╔═══╝ ██║
#  ██║     ███████╗██║  ██║███████║██║  ██╗    ██║  ██║██║     ██║
#  ╚═╝     ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝   ╚═╝  ╚═╝╚═╝     ╚═╝
# ═══════════════════════════════════════════════════════════════
# 🌐 Flask API — يشتغل على بورت 5000 في Thread منفصل
#    kobbtan.com يوجّه /api/* لـ localhost:5000/api/*
#    عن طريق Nginx reverse proxy
# ═══════════════════════════════════════════════════════════════

flask_app = Flask(__name__)
CORS(flask_app)  # قبول كل الـ origins (Vercel + kobbtan.com + localhost)

# helper: تشغيل async من context عادي (للـ Flask routes)
def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


def json_safe(obj):
    """تحويل أي dict من قاعدة البيانات لـ JSON-safe dict"""
    if obj is None:
        return None
    result = {}
    for k, v in obj.items():
        if isinstance(v, (int, float, str, bool, type(None))):
            result[k] = v
        else:
            result[k] = str(v)
    return result


@flask_app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
    return response


# ── GET /api/user/<user_id> ──────────────────────────────────────
@flask_app.route('/api/user/<int:user_id>', methods=['GET', 'OPTIONS'])
def api_get_user(user_id):
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    try:
        user = run_async(db.get_user(user_id))
        if not user:
            return jsonify({"error": "not_found"}), 404
        return jsonify(json_safe(user))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── GET /api/user/<user_id>/transactions ────────────────────────
@flask_app.route('/api/user/<int:user_id>/transactions', methods=['GET', 'OPTIONS'])
def api_get_transactions(user_id):
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    try:
        txs = run_async(db.get_transactions(user_id))
        return jsonify([json_safe(t) for t in txs])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── GET /api/leaderboard ─────────────────────────────────────────
@flask_app.route('/api/leaderboard', methods=['GET', 'OPTIONS'])
def api_leaderboard():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    try:
        lb = run_async(db.get_leaderboard(20))
        return jsonify([json_safe(u) for u in lb])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── GET /api/stats ───────────────────────────────────────────────
@flask_app.route('/api/stats', methods=['GET', 'OPTIONS'])
def api_stats():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    try:
        stats = run_async(db.get_stats())
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── GET /api/health ──────────────────────────────────────────────
@flask_app.route('/api/health', methods=['GET'])
def api_health():
    return jsonify({"status": "ok", "bot": "kobbtan.com", "version": "2.0"})


def start_api_server():
    """يشغل Flask في Thread خلفي — لا يأثر على البوت"""
    import os
    import logging as _log
    _log.getLogger('werkzeug').setLevel(_log.CRITICAL)
    # Railway بيحدد الـ PORT تلقائياً، لو مش موجود نستخدم 8080
    port = int(os.environ.get('PORT', 8080))
    flask_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)


# ═══════════════════════════════════════════════════════════════
#   TRANSACTION HELPER في قاعدة البيانات (مطلوب للـ API)
# ═══════════════════════════════════════════════════════════════
# نضيف method مؤقتة لـ DB class — لو مش موجودة
if not hasattr(DB, 'get_transactions'):
    async def _get_transactions(self, user_id, limit=20):
        async with aiosqlite.connect(self.path) as _db:
            _db.row_factory = aiosqlite.Row
            cur = await _db.execute(
                "SELECT * FROM transactions WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit)
            )
            return [dict(r) for r in await cur.fetchall()]
    DB.get_transactions = _get_transactions


def is_admin(uid): return uid in ADMIN_IDS


def level_info(total_earned):
    current = LEVELS[0]
    next_lv = None
    for i, lv in enumerate(LEVELS):
        if total_earned >= lv["min_earned"]:
            current = lv
            if i + 1 < len(LEVELS):
                next_lv = LEVELS[i + 1]
    return current, next_lv


def fmt_balance(amount):
    return f"{amount:.2f}"


# fmt_balance: يعرض الرصيد بالجنيه مباشرة (الرصيد مخزن بالجنيه)

BOT_IMAGE_URL = "https://i.postimg.cc/zGWh2DtJ/IMG-20260413-012746-325.jpg"


async def send_photo_msg(target, text, parse_mode="HTML", reply_markup=None):
    """إرسال رسالة مع صورة البوت كـ caption"""
    kwargs = {"caption": text, "parse_mode": parse_mode}
    if reply_markup:
        kwargs["reply_markup"] = reply_markup
    try:
        await target.send_photo(photo=BOT_IMAGE_URL, **kwargs)
    except Exception:
        # fallback لو الصورة فشلت
        kwargs2 = {"text": text, "parse_mode": parse_mode}
        if reply_markup:
            kwargs2["reply_markup"] = reply_markup
        await target.send_message(**kwargs2)


async def reply_photo(update, text, parse_mode="HTML", reply_markup=None):
    """رد على رسالة المستخدم بصورة + نص"""
    await send_photo_msg(update.effective_chat, text, parse_mode, reply_markup)


async def bot_send_photo(bot, chat_id, text, parse_mode="HTML", reply_markup=None):
    """إرسال صورة + نص لـ chat_id محدد"""
    kwargs = {"caption": text, "parse_mode": parse_mode}
    if reply_markup:
        kwargs["reply_markup"] = reply_markup
    try:
        await bot.send_photo(chat_id=chat_id, photo=BOT_IMAGE_URL, **kwargs)
    except Exception:
        kwargs2 = {"text": text, "parse_mode": parse_mode}
        if reply_markup:
            kwargs2["reply_markup"] = reply_markup
        await bot.send_message(chat_id=chat_id, **kwargs2)


async def edit_msg(query, text, parse_mode="HTML", reply_markup=None):
    """
    يعدّل الرسالة الحالية سواء كانت صورة (caption) أو نص عادي.
    يحل مشكلة عدم استجابة الأزرار لأن edit_message_text تفشل على رسائل الصور.
    """
    kwargs = {"parse_mode": parse_mode}
    if reply_markup:
        kwargs["reply_markup"] = reply_markup
    try:
        # الرسالة فيها صورة → نعدّل الـ caption
        if query.message and query.message.photo:
            await query.edit_message_caption(caption=text, **kwargs)
        else:
            await query.edit_message_text(text=text, **kwargs)
    except Exception:
        # fallback: ابعت رسالة جديدة
        chat_id = query.message.chat_id if query.message else query.from_user.id
        kwargs2 = {"text": text, "parse_mode": parse_mode}
        if reply_markup:
            kwargs2["reply_markup"] = reply_markup
        await query._bot.send_message(chat_id=chat_id, **kwargs2)


async def force_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """التحقق من الاشتراك الإجباري. True = الاشتراك مكتمل"""
    user_id = update.effective_user.id
    if is_admin(user_id):
        return True
    not_joined = await db.check_force_channels(user_id, context.bot)
    if not not_joined:
        return True
    # بناء الأزرار
    buttons = []
    for ch in not_joined:
        link = ch.get("invite_link") if ch.get("is_private") else ch.get("link")
        buttons.append([InlineKeyboardButton(f"{ch['name']}", url=link, api_kwargs={"icon_custom_emoji_id": "6039731759237567238"})])
    buttons.append([InlineKeyboardButton("تحققت من الاشتراك", callback_data="check_force_sub", api_kwargs={"icon_custom_emoji_id": "5974587361739151285", "style": "success"})])
    text = (
        "<tg-emoji emoji-id='5855178350263276469'>⚠️</tg-emoji> <b>يجب الاشتراك في القنوات التالية أولاً:</b>\n\n"
        + "\n".join(f"• {ch['name']}" for ch in not_joined)
        + "\n\nبعد الاشتراك اضغط <tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji>"
    )
    if update.callback_query:
        await update.callback_query.answer("⚠️ اشترك في القنوات أولاً!", show_alert=True)
        try:
            await edit_msg(update.callback_query, text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(buttons))
        except:
            await reply_photo(update, text, reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await reply_photo(update, text, reply_markup=InlineKeyboardMarkup(buttons))
    return False


# ─────────────────────────── KEYBOARDS ───────────────────────────

def main_kb(user):
    vip_icon = "5114039184507536021" if user.get("is_vip") else "5012839657545663163"
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("المهام اليومية", callback_data="tasks",          api_kwargs={"style": "success", "icon_custom_emoji_id": "5974587361739151285"}),
            InlineKeyboardButton("الهدية اليومية", callback_data="daily_gift",     api_kwargs={"style": "success", "icon_custom_emoji_id": "5970074171449808121"}),
        ],
        [
            InlineKeyboardButton("عجلة الحظ",      callback_data="wheel",          api_kwargs={"style": "primary", "icon_custom_emoji_id": "5814263327865444782"}),
            InlineKeyboardButton("ادعُ واكسب",     callback_data="referral",       api_kwargs={"style": "primary", "icon_custom_emoji_id": "5931746304207100511"}),
        ],
        [
            InlineKeyboardButton("اسحب أرباحك",   callback_data="withdraw",        api_kwargs={"style": "danger",  "icon_custom_emoji_id": "5433983375834624526"}),
            InlineKeyboardButton("كود ترويجي",    callback_data="promo",           api_kwargs={"style": "primary", "icon_custom_emoji_id": "5159203583123522328"}),
        ],
        [
            InlineKeyboardButton("ملفي الشخصي",   callback_data="profile",         api_kwargs={"style": "primary", "icon_custom_emoji_id": vip_icon}),
            InlineKeyboardButton("المتصدرون",      callback_data="leaderboard",     api_kwargs={"style": "primary", "icon_custom_emoji_id": "5433613063754363635"}),
        ],
        [
            InlineKeyboardButton("إنجازاتي",       callback_data="achievements",    api_kwargs={"style": "primary", "icon_custom_emoji_id": "5440539497383087970"}),
            InlineKeyboardButton("التحديات الأسبوعية", callback_data="weekly_challenge", api_kwargs={"style": "primary", "icon_custom_emoji_id": "5274055917766202507"}),
        ],
        [
            InlineKeyboardButton("مزايا VIP الحصرية", callback_data="vip_info",    api_kwargs={"style": "success", "icon_custom_emoji_id": "5370715282044100355"}),
        ],
        [
            InlineKeyboardButton("شارك البوت واكسب أكثر", callback_data="referral", api_kwargs={"style": "danger", "icon_custom_emoji_id": "5445355530111437729"}),
        ],
    ])


def back_kb(target="main"):
    return InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data=target, api_kwargs={"style": "danger", "icon_custom_emoji_id": "5845688877720806733"})]])


# ─────────────────────────── USER HANDLERS ───────────────────────────

async def _generate_captcha() -> tuple:
    """يولّد سؤال رياضي عشوائي ويعيد (نص_السؤال, الإجابة)"""
    a = random.randint(2, 12)
    b = random.randint(2, 12)
    op = random.choice(["+", "-", "×"])
    if op == "+":
        ans = a + b
    elif op == "-":
        # نضمن أن الإجابة موجبة
        if a < b:
            a, b = b, a
        ans = a - b
    else:
        ans = a * b
    return f"{a} {op} {b}", ans


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = ctx.args
    referred_by = None
    if args and args[0].startswith("REF"):
        try:
            referred_by = int(args[0][3:])
            if referred_by == user.id:
                referred_by = None
        except:
            pass

    # تحقق لو العضو موجود أصلاً
    db_user = await db.get_user(user.id)
    if db_user:
        # عضو قديم - ادخل عادي بدون CAPTCHA
        if db_user.get("is_banned"):
            await reply_photo(update,
                f"🚫 تم حظر حسابك.\nالسبب: {db_user.get('ban_reason') or 'مخالفة الشروط'}"
            )
            return
        maintenance = await db.get("maintenance_mode")
        if maintenance and not is_admin(user.id):
            await update.message.reply_text(
                "<tg-emoji emoji-id='5855065341083784332'>🔧</tg-emoji> البوت في وضع الصيانة مؤقتاً. عد لاحقاً!",
                parse_mode="HTML"
            )
            return
        if not await force_check(update, ctx):
            return
        bal = db_user["balance"]
        lv, _ = level_info(db_user["total_earned"])
        text = (
            f"<tg-emoji emoji-id='5433613063754363635'>🔖</tg-emoji> <b>مرحباً بعودتك <i>{user.first_name}</i></b>\n\n"
            f"<tg-emoji emoji-id='5433983375834624526'>💸</tg-emoji> <b>رصيدك الحالي:</b>\n"
            f"جنيه {bal:.2f}\n\n"
            f"<tg-emoji emoji-id='5440539497383087970'>🏅</tg-emoji> مستواك: {lv['name']}\n"
            f"<tg-emoji emoji-id='5855190238732751076'>🔥</tg-emoji> الاتساق: {db_user['streak']} يوم متتالي"
        )
        await reply_photo(update, text, reply_markup=main_kb(db_user))
        return

    # عضو جديد - تحقق الصيانة أولاً
    maintenance = await db.get("maintenance_mode")
    if maintenance and not is_admin(user.id):
        await reply_photo(update,
            "<tg-emoji emoji-id='5855065341083784332'>🔧</tg-emoji> البوت في وضع الصيانة مؤقتاً. عد لاحقاً!"
        )
        return

    # إرسال CAPTCHA للعضو الجديد
    question, ans = await _generate_captcha()
    CAPTCHA_PENDING[user.id] = {
        "answer": ans,
        "referred_by": referred_by,
        "attempts": 0
    }
    await reply_photo(update,
        f"<tg-emoji emoji-id='5855178350263276469'>⚠️</tg-emoji> <b>تحقق سريع قبل الدخول!</b>\n\n"
        f"🧮 <b>كام ناتج:</b>  <code>{question} = ؟</code>\n\n"
        f"اكتب الإجابة برقم فقط 👇"
    )


async def handle_captcha_answer(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """يتعامل مع إجابة الـ CAPTCHA للأعضاء الجدد"""
    user = update.effective_user
    if user.id not in CAPTCHA_PENDING:
        return  # مش في CAPTCHA، handle_text هيتولى

    raw = update.message.text.strip()
    try:
        answer = int(raw)
    except ValueError:
        await reply_photo(update, "❌ اكتب رقم صحيح فقط!")
        return

    captcha = CAPTCHA_PENDING[user.id]
    if answer == captcha["answer"]:
        # إجابة صح - سجل العضو
        del CAPTCHA_PENDING[user.id]
        referred_by = captcha["referred_by"]

        db_user, is_new = await db.get_or_create(
            user.id, user.username or "", user.full_name or "", referred_by
        )

        # إشعار من دعاه (لو دخل برابط)
        if referred_by and is_new:
            try:
                ref_user = await db.get_user(referred_by)
                r1 = await db.get("referral_reward_l1")
                await bot_send_photo(ctx.bot, referred_by,
                    f"<tg-emoji emoji-id='5931746304207100511'>🔗</tg-emoji> <b>دعوة جديدة!</b>\n\n"
                    f"<tg-emoji emoji-id='5012839657545663163'>👤</tg-emoji> <b>{user.full_name}</b> انضم عن طريق رابطك!\n"
                    f"<tg-emoji emoji-id='4958926882994127612'>💰</tg-emoji> ربحت <b>{r1} جنيه</b> مكافأة دعوة\n"
                    f"<tg-emoji emoji-id='5931746304207100511'>🔗</tg-emoji> إجمالي دعواتك: <b>{(ref_user['ref_count'] if ref_user else 0)} دعوة</b>"
                )
            except Exception:
                pass

        # رسالة الترحيب
        text_msg = (
            f"✅ <b>إجابة صحيحة! أهلاً بك <i>{user.first_name}</i> 🎉</b>\n\n"
            f"<tg-emoji emoji-id='5433983375834624526'>💸</tg-emoji> <b>اكسب بسهولة عبر:</b>\n"
            f"• دعوة الأصدقاء\n"
            f"• المهام اليومية\n\n"
            f"<tg-emoji emoji-id='5433983375834624526'>💸</tg-emoji> <b>رصيدك الحالي:</b>\n"
            f"جنيه 0.00"
        )
        await reply_photo(update, text_msg, reply_markup=main_kb(db_user))

    else:
        # إجابة غلط
        captcha["attempts"] += 1
        if captcha["attempts"] >= 3:
            del CAPTCHA_PENDING[user.id]
            await reply_photo(update,
                "❌ <b>فشلت 3 مرات!</b>\nابعت /start تاني لو عايز تحاول."
            )
        else:
            remaining = 3 - captcha["attempts"]
            question, ans = await _generate_captcha()
            captcha["answer"] = ans
            await reply_photo(update,
                f"❌ إجابة غلط! باقي <b>{remaining}</b> محاولات.\n\n"
                f"🧮 <b>حاول تاني:</b>  <code>{question} = ؟</code>"
            )


async def cb_main(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user = q.from_user
    db_user = await db.get_user(user.id)
    if not db_user:
        return
    if not await force_check(update, ctx):
        return
    lv, _ = level_info(db_user["total_earned"])
    text = (
        f"<tg-emoji emoji-id='5197708768091061888'>🏠</tg-emoji> <b>القائمة الرئيسية</b>\n\n"
        f"<tg-emoji emoji-id='4958926882994127612'>💰</tg-emoji> رصيدك: <b>جنيه {db_user['balance']:.2f}</b>\n"
        f"<tg-emoji emoji-id='5440539497383087970'>🏅</tg-emoji> المستوى: {lv['name']}\n"
        f"<tg-emoji emoji-id='5855190238732751076'>🔥</tg-emoji> الاتساق: {db_user['streak']} يوم"
    )
    await edit_msg(q, text, parse_mode="HTML", reply_markup=main_kb(db_user))


async def cb_check_force(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    not_joined = await db.check_force_channels(q.from_user.id, ctx.bot)
    if not_joined:
        await q.answer("❌ لم تشترك بعد في كل القنوات!", show_alert=True)
    else:
        await q.answer("✅ رائع! تم التحقق.", show_alert=True)
        db_user = await db.get_user(q.from_user.id)
        await edit_msg(q, 
            "<tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji> <b>تم التحقق من اشتراكك!</b>\nيمكنك الآن استخدام البوت.",
            parse_mode="HTML",
            reply_markup=main_kb(db_user)
        )


async def cb_profile(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not await force_check(update, ctx):
        return
    u = await db.get_user(q.from_user.id)
    if not u:
        return
    lv, nxt = level_info(u["total_earned"])
    vip_str = "<tg-emoji emoji-id='5370715282044100355'>⭐</tg-emoji> VIP" if u["is_vip"] else "عادي"
    next_str = f"\n<tg-emoji emoji-id='5918243322165465038'>📈</tg-emoji> للمستوى التالي: {nxt['name']} (يحتاج {nxt['min_earned']} جنيه)" if nxt else "\n<tg-emoji emoji-id='5370715282044100355'>🌟</tg-emoji> أعلى مستوى!"
    earned_list = json.loads(u.get("achievements") or "[]")
    ach_count = len(earned_list)
    text = (
        f"<tg-emoji emoji-id='5012839657545663163'>👤</tg-emoji> <b>ملفك الشخصي</b>\n\n"
        f"<tg-emoji emoji-id='5794357309794686314'>🆔</tg-emoji> ID: `{u['user_id']}`\n"
        f"<tg-emoji emoji-id='5012839657545663163'>👤</tg-emoji> الاسم: {u['full_name']}\n"
        f"<tg-emoji emoji-id='4958926882994127612'>💰</tg-emoji> الرصيد: <b>جنيه {u['balance']:.2f}</b>\n"
        f"<tg-emoji emoji-id='5918243322165465038'>📈</tg-emoji> إجمالي الأرباح: جنيه {u['total_earned']:.2f}\n"
        f"<tg-emoji emoji-id='5433983375834624526'>💸</tg-emoji> إجمالي السحب: جنيه {u['total_withdrawn']:.2f}\n"
        f"<tg-emoji emoji-id='5931746304207100511'>🔗</tg-emoji> الدعوات: {u['ref_count']} (مستوى 2: {u['ref_l2_count']})\n"
        f"<tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji> المهام المكتملة: {u['tasks_done']}\n"
        f"<tg-emoji emoji-id='5440539497383087970'>🏅</tg-emoji> المستوى: {lv['name']}{next_str}\n"
        f"<tg-emoji emoji-id='5855190238732751076'>🔥</tg-emoji> الاتساق: {u['streak']} يوم متتالي\n"
        f"<tg-emoji emoji-id='5433613063754363635'>🏆</tg-emoji> الإنجازات: {ach_count}/{len(ACHIEVEMENTS)}\n"
        f"<tg-emoji emoji-id='5370715282044100355'>⭐</tg-emoji> الحالة: {vip_str}\n"
        f"<tg-emoji emoji-id='5274055917766202507'>📅</tg-emoji> التسجيل: {(u['join_date'] or '')[:10]}"
    )
    await edit_msg(q, text, parse_mode="HTML", reply_markup=back_kb("main"))


async def cb_achievements(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    u = await db.get_user(q.from_user.id)
    earned = json.loads(u.get("achievements") or "[]")
    text = "<tg-emoji emoji-id='5433613063754363635'>🏆</tg-emoji> <b>إنجازاتك</b>\n\n"
    for key, ach in ACHIEVEMENTS.items():
        status = "<tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji>" if key in earned else "<tg-emoji emoji-id='4902389625726698210'>🔒</tg-emoji>"
        reward_str = f" (+{ach['reward']} جنيه)" if ach['reward'] > 0 else ""
        text += f"{status} <b>{ach['name']}</b>{reward_str}\n   _{ach['desc']}_\n\n"
    await edit_msg(q, text, parse_mode="HTML", reply_markup=back_kb("main"))


async def cb_leaderboard(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    leaders = await db.get_leaderboard(10)
    medals = ["🥇", "🥈", "🥉"] + [f"{i}️⃣" for i in range(4, 11)]
    text = "<tg-emoji emoji-id='5433613063754363635'>🏆</tg-emoji> <b>المتصدرون - أفضل 10 كاسبين</b> <tg-emoji emoji-id='5433613063754363635'>🏆</tg-emoji>\n\n"
    for i, u in enumerate(leaders):
        name = (u["full_name"] or "مجهول")[:15]
        vip_tag = "<tg-emoji emoji-id='5370715282044100355'>⭐</tg-emoji>" if u.get("is_vip") else ""
        text += f"{medals[i]} {vip_tag}<b>{name}</b>: `{fmt_balance(u['total_earned'])} جنيه`\n"
    text += "\n<tg-emoji emoji-id='5434045652860416220'>💡</tg-emoji> <b>أكمل المهام وادعُ أصدقاءك لتصعد للقمة!</b>"
    await edit_msg(q, text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("ادعُ واصعد للمتصدرين 🚀", callback_data="referral", api_kwargs={"icon_custom_emoji_id": "5931746304207100511", "style": "primary"})],
        [InlineKeyboardButton("رجوع", callback_data="main", api_kwargs={"icon_custom_emoji_id": "5845688877720806733", "style": "danger"})],
    ]))


async def cb_vip_info(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    mult = await db.get("vip_multiplier")
    text = (
        f"<tg-emoji emoji-id='5370715282044100355'>⭐</tg-emoji>✨ <b>نظام VIP الحصري</b> ✨<tg-emoji emoji-id='5370715282044100355'>⭐</tg-emoji>\n\n"
        f"╔══════════════════╗\n"
        f"║  <tg-emoji emoji-id='5764978573848877254'>🎯</tg-emoji> <b>مزايا VIP الحصرية:</b>\n"
        f"║  <tg-emoji emoji-id='4958926882994127612'>💰</tg-emoji> مضاعفة كل المكافآت x{mult}\n"
        f"║  <tg-emoji emoji-id='5970074171449808121'>🎁</tg-emoji> هدية يومية مضاعفة\n"
        f"║  <tg-emoji emoji-id='5814263327865444782'>🎰</tg-emoji> عجلة حظ بجوائز مضاعفة\n"
        f"║  <tg-emoji emoji-id='5931795421453097161'>⚡</tg-emoji> أولوية في معالجة السحب\n"
        f"║  <tg-emoji emoji-id='5114039184507536021'>👑</tg-emoji> شارة VIP مميزة <tg-emoji emoji-id='5370715282044100355'>⭐</tg-emoji>\n"
        f"║  <tg-emoji emoji-id='4958926882994127612'>💵</tg-emoji> مكافآت المهام مضاعفة\n"
        f"╚══════════════════╝\n\n"
        f"<tg-emoji emoji-id='5433791914782503352'>📩</tg-emoji> <b>للحصول على VIP تواصل مع الأدمن الآن!</b>"
    )
    await edit_msg(q, text, parse_mode="HTML", reply_markup=back_kb("main"))


# ─────────────────────────── TASKS ───────────────────────────

async def cb_tasks(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not await force_check(update, ctx):
        return
    tasks = await db.get_tasks(active_only=True)
    if not tasks:
        await edit_msg(q, "😔 لا توجد مهام متاحة الآن. عد لاحقاً!", reply_markup=back_kb("main"))
        return
    text = "<tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji> <b>المهام اليومية</b>\nأكمل المهام واحصل على مكافآت <tg-emoji emoji-id='4958926882994127612'>💰</tg-emoji>\n\n"
    buttons = []
    for t in tasks:
        done = await db.is_task_done(q.from_user.id, t["task_id"])
        icon = "<tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji>" if done else "⭕"
        priv = "<tg-emoji emoji-id='4902389625726698210'>🔒</tg-emoji>" if t.get("is_private") else ""
        buttons.append([InlineKeyboardButton(
            f"{icon}{priv} {t['title']} ← {t['reward']} جنيه",
            callback_data=f"task_{t['task_id']}"
        )])
    buttons.append([InlineKeyboardButton("رجوع", callback_data="main", api_kwargs={"icon_custom_emoji_id": "5845688877720806733", "style": "danger"})])
    await edit_msg(q, text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(buttons))


async def cb_task_view(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    tid = int(q.data.split("_")[1])
    task = await db.get_task(tid)
    if not task:
        return
    done = await db.is_task_done(q.from_user.id, tid)
    u = await db.get_user(q.from_user.id)
    reward = task["reward"]
    if u and u.get("is_vip"):
        mult = await db.get("vip_multiplier")
        reward = round(reward * mult, 2)
    vip_note = " <b>(<tg-emoji emoji-id='5370715282044100355'>⭐</tg-emoji> VIP مضاعف)</b>" if u and u.get("is_vip") else ""
    priv_note = "\n<tg-emoji emoji-id='4902389625726698210'>🔒</tg-emoji> <b>قناة خاصة</b> - استخدم رابط الدعوة" if task.get("is_private") else ""
    text = (
        f"<tg-emoji emoji-id='5197269100878907942'>📋</tg-emoji> <b>{task['title']}</b>\n\n"
        f"<tg-emoji emoji-id='5861505966666695398'>📝</tg-emoji> {task['description']}{priv_note}\n\n"
        f"<tg-emoji emoji-id='4958926882994127612'>💰</tg-emoji> المكافأة: <b>{reward} جنيه</b>{vip_note}\n\n"
        + ("<tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji> <b>أكملت هذه المهمة بالفعل!</b>" if done else "<tg-emoji emoji-id='5100479302739165822'>👇</tg-emoji> اشترك ثم اضغط التحقق")
    )
    if done:
        kb = [[InlineKeyboardButton("رجوع للمهام", callback_data="tasks", api_kwargs={"icon_custom_emoji_id": "5845688877720806733", "style": "danger"})]]
    else:
        kb = []
        link = task.get("invite_link") if task.get("is_private") else task.get("channel_link")
        if link:
            kb.append([InlineKeyboardButton("انضم للقناة/المجموعة", url=link, api_kwargs={"icon_custom_emoji_id": "6039731759237567238"})])
        kb.append([InlineKeyboardButton("تحقق من الاشتراك", callback_data=f"verify_{tid}", api_kwargs={"icon_custom_emoji_id": "5974587361739151285", "style": "success"})])
        kb.append([InlineKeyboardButton("رجوع", callback_data="tasks", api_kwargs={"icon_custom_emoji_id": "5845688877720806733", "style": "danger"})])
    await edit_msg(q, text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))


async def cb_verify(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer("⏳ جاري التحقق...")
    tid = int(q.data.split("_")[1])
    task = await db.get_task(tid)
    if not task:
        return
    if await db.is_task_done(q.from_user.id, tid):
        await q.answer("✅ أكملت هذه المهمة مسبقاً!", show_alert=True)
        return
    # التحقق من الاشتراك
    subscribed = True
    if task.get("channel_id") and task.get("task_type") == "subscribe":
        try:
            member = await ctx.bot.get_chat_member(task["channel_id"], q.from_user.id)
            subscribed = member.status not in [ChatMember.LEFT, ChatMember.BANNED]
        except TelegramError:
            subscribed = True  # إذا فشل التحقق، نعطي المكافأة
    if not subscribed:
        link = task.get("invite_link") if task.get("is_private") else task.get("channel_link")
        kb = [
            [InlineKeyboardButton("اشترك الآن", url=link, api_kwargs={"icon_custom_emoji_id": "6039731759237567238"})] if link else [],
            [InlineKeyboardButton("تحقق مرة أخرى", callback_data=f"verify_{tid}", api_kwargs={"icon_custom_emoji_id": "5906823124384486718", "style": "primary"})],
            [InlineKeyboardButton("رجوع", callback_data="tasks", api_kwargs={"icon_custom_emoji_id": "5845688877720806733", "style": "danger"})],
        ]
        kb = [row for row in kb if row]
        await edit_msg(q, "<tg-emoji emoji-id='4958526153955476488'>❌</tg-emoji> <b>لم تشترك بعد!</b>\nاشترك أولاً ثم اضغط تحقق.", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))
        return
    u = await db.get_user(q.from_user.id)
    reward = task["reward"]
    if u and u.get("is_vip"):
        reward = round(reward * await db.get("vip_multiplier"), 2)
    weekly_bonus = await db.complete_task(q.from_user.id, tid, reward)
    extra = f"\n<tg-emoji emoji-id='5433613063754363635'>🏆</tg-emoji> <b>أنجزت التحدي الأسبوعي! +{weekly_bonus} جنيه</b>" if weekly_bonus else ""
    # رسالة إنجاز مميزة
    congrats_msgs = [
        "<tg-emoji emoji-id='5855190238732751076'>🔥</tg-emoji> عظيم! استمر!",
        "<tg-emoji emoji-id='5231247330186895689'>💪</tg-emoji> أنت نجم!",
        "<tg-emoji emoji-id='5931795421453097161'>⚡</tg-emoji> رائع جداً!",
        "<tg-emoji emoji-id='5370715282044100355'>🌟</tg-emoji> ممتاز!",
        "<tg-emoji emoji-id='5764978573848877254'>🎯</tg-emoji> مذهل!",
    ]
    congrats = random.choice(congrats_msgs)
    await edit_msg(q, 
        f"<tg-emoji emoji-id='4956596167451346576'>🎉</tg-emoji> <b>تهانيك! {congrats}</b>\n\n"
        f"<tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji> أكملت: <b>{task['title']}</b>\n"
        f"╔══════════════════╗\n"
        f"║  <tg-emoji emoji-id='4958926882994127612'>💰</tg-emoji> <b>{reward} جنيه</b> أُضيفت لرصيدك!\n"
        f"╚══════════════════╝"
        f"{extra}",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("مهام أخرى", callback_data="tasks", api_kwargs={"icon_custom_emoji_id": "5974587361739151285", "style": "success"})],
            [InlineKeyboardButton("الرئيسية", callback_data="main", api_kwargs={"icon_custom_emoji_id": "5845688877720806733", "style": "danger"})],
        ])
    )


# ─────────────────────────── DAILY GIFT ───────────────────────────

async def cb_daily_gift(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not await force_check(update, ctx):
        return
    reward, ok, next_t = await db.claim_gift(q.from_user.id)
    if ok:
        gifts_emojis = ["<tg-emoji emoji-id='5970074171449808121'>🎁</tg-emoji>", "🎀", "<tg-emoji emoji-id='4956596167451346576'>🎊</tg-emoji>", "💝", "🎈"]
        emoji = random.choice(gifts_emojis)
        text = (
            f"{emoji} <b>حصلت على هديتك اليومية!</b> {emoji}\n\n"
            f"╔══════════════════╗\n"
            f"║  <tg-emoji emoji-id='4958926882994127612'>💰</tg-emoji> <b>{reward} جنيه</b> أُضيفت لرصيدك! <tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji>\n"
            f"╚══════════════════╝\n\n"
            f"<tg-emoji emoji-id='5782749628101300654'>🔔</tg-emoji> عد غداً لهدية جديدة!\n"
            f"<tg-emoji emoji-id='5434045652860416220'>💡</tg-emoji> <b>نصيحة:</b> ادعُ أصدقاءك لمضاعفة دخلك <tg-emoji emoji-id='5861568308116984245'>🚀</tg-emoji>"
        )
    else:
        hrs = mins = 0
        if next_t:
            diff = next_t - datetime.datetime.now()
            hrs = int(diff.total_seconds() // 3600)
            mins = int((diff.total_seconds() % 3600) // 60)
        text = f"<tg-emoji emoji-id='5992452437120652643'>⏳</tg-emoji> <b>أخذت هديتك اليوم!</b>\n<tg-emoji emoji-id='5854847234054558104'>⏰</tg-emoji> العودة بعد: {hrs}h {mins}m\n\n<tg-emoji emoji-id='5764978573848877254'>🎯</tg-emoji> استمر في المهام للكسب أكثر!"
    await edit_msg(q, text, parse_mode="HTML", reply_markup=back_kb("main"))


# ─────────────────────────── WHEEL ───────────────────────────

async def cb_wheel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not await force_check(update, ctx):
        return
    u = await db.get_user(q.from_user.id)
    prizes = await db.get("wheel_prizes")
    last_wheel = u.get("last_wheel")
    can_spin = True
    if last_wheel:
        diff = (datetime.datetime.now() - datetime.datetime.fromisoformat(last_wheel)).total_seconds()
        can_spin = diff >= 86400
    text = (
        f"<tg-emoji emoji-id='5814263327865444782'>🎰</tg-emoji> <b>عجلة الحظ</b>\n\n"
        f"<tg-emoji emoji-id='5764978573848877254'>🎯</tg-emoji> الجوائز المتاحة:\n"
        + "\n".join(f"  <tg-emoji emoji-id='4958926882994127612'>💰</tg-emoji> {p} جنيه" for p in sorted(prizes, reverse=True))
        + f"\n\n{'✅ يمكنك الدوران الآن!' if can_spin else '⏳ دورت اليوم بالفعل!'}"
    )
    if can_spin:
        kb = [[InlineKeyboardButton("اضغط للدوران!", callback_data="spin_wheel", api_kwargs={"icon_custom_emoji_id": "5814263327865444782", "style": "success"})],
              [InlineKeyboardButton("رجوع", callback_data="main", api_kwargs={"icon_custom_emoji_id": "5845688877720806733", "style": "danger"})]]
    else:
        if last_wheel:
            next_t = datetime.datetime.fromisoformat(last_wheel) + datetime.timedelta(days=1)
            diff = next_t - datetime.datetime.now()
            hrs = int(diff.total_seconds() // 3600)
            mins = int((diff.total_seconds() % 3600) // 60)
            text += f"\n<tg-emoji emoji-id='5854847234054558104'>⏰</tg-emoji> العودة بعد: {hrs}h {mins}m"
        kb = [[InlineKeyboardButton("رجوع", callback_data="main", api_kwargs={"icon_custom_emoji_id": "5845688877720806733", "style": "danger"})]]
    await edit_msg(q, text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))


async def cb_spin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer("🎰 جاري الدوران... 🌀🌀🌀")
    prize, ok, _ = await db.spin_wheel(q.from_user.id)
    if ok:
        prizes = await db.get("wheel_prizes")
        is_jackpot = prize >= max(prizes)
        if is_jackpot:
            jackpot_text = (
                "\n\n<tg-emoji emoji-id='4956596167451346576'>🎊</tg-emoji><tg-emoji emoji-id='4956596167451346576'>🎊</tg-emoji><tg-emoji emoji-id='4956596167451346576'>🎊</tg-emoji> <b>JACKPOT!!</b> <tg-emoji emoji-id='4956596167451346576'>🎊</tg-emoji><tg-emoji emoji-id='4956596167451346576'>🎊</tg-emoji><tg-emoji emoji-id='4956596167451346576'>🎊</tg-emoji>\n"
                "╔══════════════════╗\n"
                "║  <tg-emoji emoji-id='5433613063754363635'>🏆</tg-emoji> الجائزة الكبرى! <tg-emoji emoji-id='5433613063754363635'>🏆</tg-emoji>  ║\n"
                "╚══════════════════╝"
            )
        else:
            jackpot_text = ""
        # رسالة مشجعة عشوائية
        congrats = random.choice([
            "<tg-emoji emoji-id='5855190238732751076'>🔥</tg-emoji> عظيم!", "<tg-emoji emoji-id='5370715282044100355'>🌟</tg-emoji> رائع!", "<tg-emoji emoji-id='5231247330186895689'>💪</tg-emoji> استمر!", "<tg-emoji emoji-id='5764978573848877254'>🎯</tg-emoji> ممتاز!", "<tg-emoji emoji-id='5931795421453097161'>⚡</tg-emoji> مذهل!"
        ])
        text = (
            f"<tg-emoji emoji-id='5814263327865444782'>🎰</tg-emoji> <b>نتيجة عجلة الحظ</b>\n\n"
            f"╔══════════════════╗\n"
            f"║  <tg-emoji emoji-id='4956596167451346576'>🎉</tg-emoji> ربحت: <b>{prize} جنيه</b>! {congrats}\n"
            f"╚══════════════════╝"
            f"{jackpot_text}\n\n"
            f"<tg-emoji emoji-id='4958926882994127612'>💰</tg-emoji> أُضيفت لرصيدك فوراً!\n"
            f"<tg-emoji emoji-id='5782749628101300654'>🔔</tg-emoji> عد غداً لدورة جديدة!"
        )
    else:
        text = "<tg-emoji emoji-id='5992452437120652643'>⏳</tg-emoji> دورت العجلة اليوم بالفعل! عد غداً."
    await edit_msg(q, text, parse_mode="HTML", reply_markup=back_kb("wheel"))


# ─────────────────────────── REFERRAL ───────────────────────────

async def cb_referral(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not await force_check(update, ctx):
        return
    u = await db.get_user(q.from_user.id)
    bot_info = await ctx.bot.get_me()
    link = f"https://t.me/{bot_info.username}?start={u['ref_code']}"
    r1 = await db.get("referral_reward_l1")
    r2 = await db.get("referral_reward_l2")
    r3 = await db.get("referral_reward_l3")
    total_ref_earnings = (u["ref_count"] * r1) + (u["ref_l2_count"] * r2)
    text = (
        f"<tg-emoji emoji-id='5931746304207100511'>🔗</tg-emoji><tg-emoji emoji-id='4958926882994127612'>💰</tg-emoji> <b>نظام الدعوة متعدد المستويات</b>\n\n"
        f"╔══════════════════╗\n"
        f"║  🥇 المستوى 1: <b>{r1} جنيه</b> لكل دعوة مباشرة\n"
        f"║  🥈 المستوى 2: <b>{r2} جنيه</b> (دعوة دعوتك)\n"
        f"║  🥉 المستوى 3: <b>{r3} جنيه</b>\n"
        f"╚══════════════════╝\n\n"
        f"<tg-emoji emoji-id='5012839657545663163'>👥</tg-emoji> دعوتك: <b>{u['ref_count']}<b> مباشر | </b>{u['ref_l2_count']}</b> مستوى 2\n"
        f"<tg-emoji emoji-id='4958926882994127612'>💵</tg-emoji> أرباح الدعوات: <b>{fmt_balance(total_ref_earnings)} جنيه</b>\n\n"
        f"<tg-emoji emoji-id='5931746304207100511'>🔗</tg-emoji> <b>رابطك الخاص — شاركه الآن:</b>\n{link}\n\n"
        f"<tg-emoji emoji-id='5855190238732751076'>🔥</tg-emoji> <b>كل ما شاركت أكتر، كسبت أكتر!</b>"
    )
    share_text = f"💰 انضم معي في بوت الكسب الاحترافي وابدأ تكسب فلوس حقيقية! 🚀\nرابط التسجيل: {link}"
    kb = [
        [InlineKeyboardButton("📤 شارك الرابط في أي مكان", switch_inline_query=share_text, api_kwargs={"icon_custom_emoji_id": "5861568308116984245"})],
        [InlineKeyboardButton("نسخ الرابط", callback_data="referral", api_kwargs={"icon_custom_emoji_id": "5197269100878907942", "style": "primary"})],
        [InlineKeyboardButton("رجوع", callback_data="main", api_kwargs={"icon_custom_emoji_id": "5845688877720806733", "style": "danger"})],
    ]
    await edit_msg(q, text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))


# ─────────────────────────── WITHDRAW ───────────────────────────

async def cb_withdraw(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not await force_check(update, ctx):
        return
    u = await db.get_user(q.from_user.id)
    min_w = await db.get("min_withdraw")
    bal = u["balance"]
    text = (
        f"<tg-emoji emoji-id='5433983375834624526'>💸</tg-emoji> <b>طلب سحب</b>\n\n"
        f"<tg-emoji emoji-id='4958926882994127612'>💰</tg-emoji> رصيدك: <b>جنيه {bal:.2f}</b>\n"
        f"<tg-emoji emoji-id='5197269100878907942'>📋</tg-emoji> الحد الأدنى: <b>جنيه {min_w:.2f}</b>\n\n"
    )
    if bal < min_w:
        text += f"<tg-emoji emoji-id='4958526153955476488'>❌</tg-emoji> تحتاج <b>{fmt_balance(min_w - bal)} جنيه</b> إضافية للسحب."
        await edit_msg(q, text, parse_mode="HTML", reply_markup=back_kb("main"))
        return
    text += "اختر طريقة الدفع:"
    kb = [[InlineKeyboardButton(name, callback_data=f"wmethod_{mid}", api_kwargs={"style": "primary", **({"icon_custom_emoji_id": eid} if eid else {})})] for mid, (name, eid) in WITHDRAW_METHODS.items()]
    kb.append([InlineKeyboardButton("رجوع", callback_data="main", api_kwargs={"icon_custom_emoji_id": "5845688877720806733", "style": "danger"})])
    await edit_msg(q, text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))


async def cb_wmethod(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    method = q.data.split("_")[1]
    ctx.user_data["w_method"] = method
    ctx.user_data["w_waiting"] = True
    u = await db.get_user(q.from_user.id)
    method_name = WITHDRAW_METHODS.get(method, (method, None))[0]
    text = (
        f"<tg-emoji emoji-id='5161427856491807309'>💳</tg-emoji> <b>{method_name}</b>\n\n"
        f"<tg-emoji emoji-id='4958926882994127612'>💰</tg-emoji> رصيدك: <b>جنيه {u['balance']:.2f}</b>\n\n"
        f"<tg-emoji emoji-id='5861505966666695398'>📝</tg-emoji> أرسل رقم محفظتك أو حسابك:"
    )
    await edit_msg(q, text, parse_mode="HTML",
                               reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("إلغاء", callback_data="main", api_kwargs={"icon_custom_emoji_id": "4958526153955476488", "style": "danger"})]]))


# ─────────────────────────── PROMO CODES ───────────────────────────

async def cb_promo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not await force_check(update, ctx):
        return
    ctx.user_data["promo_waiting"] = True
    text = (
        "<tg-emoji emoji-id='5159203583123522328'>🎟️</tg-emoji> <b>الأكواد الترويجية</b>\n\n"
        "أرسل كود الخصم للحصول على مكافأة فورية:"
    )
    await edit_msg(q, text, parse_mode="HTML",
                               reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="main", api_kwargs={"icon_custom_emoji_id": "5845688877720806733", "style": "danger"})]]))


# ─────────────────────────── WEEKLY CHALLENGE ───────────────────────────

async def cb_weekly(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    week_start = (datetime.datetime.now() - datetime.timedelta(days=datetime.datetime.now().weekday())).date().isoformat()
    async with aiosqlite.connect(DB_PATH) as db_conn:
        db_conn.row_factory = aiosqlite.Row
        cur = await db_conn.execute(
            "SELECT * FROM weekly_challenges WHERE user_id=? AND week_start=?",
            (q.from_user.id, week_start)
        )
        ch = await cur.fetchone()
    target = await db.get("weekly_challenge_tasks")
    reward = await db.get("weekly_challenge_reward")
    done_count = ch["tasks_done"] if ch else 0
    completed = ch["completed"] if ch else 0
    text = (
        f"<tg-emoji emoji-id='5274055917766202507'>📅</tg-emoji> <b>التحدي الأسبوعي</b>\n\n"
        f"<tg-emoji emoji-id='5764978573848877254'>🎯</tg-emoji> الهدف: إكمال <b>{target} مهام</b> هذا الأسبوع\n"
        f"<tg-emoji emoji-id='4958926882994127612'>💰</tg-emoji> المكافأة: <b>{reward} جنيه</b>\n\n"
        f"<tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji> أنجزت: <b>{done_count}/{target}</b> مهمة\n\n"
        + ("<tg-emoji emoji-id='4956596167451346576'>🎉</tg-emoji> <b>أنجزت التحدي وحصلت على مكافأتك!</b> <tg-emoji emoji-id='5433613063754363635'>🏆</tg-emoji>" if completed else
           f"{'🔥 أكمل المهام للفوز!' if done_count < target else ''}")
    )
    # شريط التقدم
    filled = int((done_count / target) * 10)
    bar = "█" * filled + "░" * (10 - filled)
    text += f"\n\n[{bar}] {done_count}/{target}"
    await edit_msg(q, text, parse_mode="HTML", reply_markup=back_kb("main"))


# ─────────────────────────── TEXT HANDLER ───────────────────────────

async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text.strip()

    # ─ أولاً: تحقق من CAPTCHA ─
    if user.id in CAPTCHA_PENDING:
        await handle_captcha_answer(update, ctx)
        return

    # ─ سحب - إدخال رقم الحساب ─
    if ctx.user_data.get("w_waiting"):
        ctx.user_data["w_waiting"] = False
        method = ctx.user_data.pop("w_method", "")
        u = await db.get_user(user.id)
        min_w = await db.get("min_withdraw")
        if not u or u["balance"] < min_w:
            await reply_photo(update, f"<tg-emoji emoji-id='4958526153955476488'>❌</tg-emoji> رصيدك أقل من {min_w} جنيه!")
            return
        ctx.user_data["w_confirm_method"] = method
        ctx.user_data["w_confirm_account"] = text
        method_name = WITHDRAW_METHODS.get(method, (method, None))[0]
        await reply_photo(update,
            f"<tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji> <b>تأكيد طلب السحب</b>\n\n"
            f"<tg-emoji emoji-id='4958926882994127612'>💰</tg-emoji> المبلغ: <b>جنيه {u['balance']:.2f}</b>\n"
            f"<tg-emoji emoji-id='5161427856491807309'>💳</tg-emoji> الطريقة: {method_name}\n"
            f"<tg-emoji emoji-id='5859518547859869809'>📞</tg-emoji> الحساب: `{text}`",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("تأكيد", callback_data="w_confirm", api_kwargs={"icon_custom_emoji_id": "5974587361739151285", "style": "success"}),
                 InlineKeyboardButton("إلغاء", callback_data="main", api_kwargs={"icon_custom_emoji_id": "4958526153955476488", "style": "danger"})]
            ])
        )
        return

    # ─ كود ترويجي ─
    if ctx.user_data.get("promo_waiting"):
        ctx.user_data.pop("promo_waiting")
        reward, err = await db.use_promo(text, user.id)
        if err:
            await reply_photo(update, err, reply_markup=back_kb("main"))
        else:
            await reply_photo(update,
                f"<tg-emoji emoji-id='4956596167451346576'>🎉</tg-emoji> <b>كود صحيح!</b>\n<tg-emoji emoji-id='4958926882994127612'>💰</tg-emoji> حصلت على <b>{reward} جنيه</b>!",
                reply_markup=back_kb("main")
            )
        return

    # ─── معالجة الأدمن ───
    if not is_admin(user.id):
        return
    state = ctx.user_data.get("admin_state")
    if not state:
        return

    await _admin_text_input(update, ctx, state, text)


async def cb_w_confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    method = ctx.user_data.pop("w_confirm_method", "")
    account = ctx.user_data.pop("w_confirm_account", "")
    u = await db.get_user(q.from_user.id)
    min_w = await db.get("min_withdraw")
    if not u or u["balance"] < min_w:
        await q.answer("❌ رصيد غير كافٍ!", show_alert=True)
        return
    amount = u["balance"]
    await db.create_withdrawal(q.from_user.id, amount, method, account)
    # إشعار الأدمن
    method_name = WITHDRAW_METHODS.get(method, (method, None))[0]
    for aid in ADMIN_IDS:
        try:
            await bot_send_photo(ctx.bot, aid,
                f"<tg-emoji emoji-id='5433983375834624526'>💸</tg-emoji> <b>طلب سحب جديد!</b>\n<tg-emoji emoji-id='5012839657545663163'>👤</tg-emoji> {u['full_name']}\n<tg-emoji emoji-id='5794357309794686314'>🆔</tg-emoji> `{q.from_user.id}`\n"
                f"<tg-emoji emoji-id='4958926882994127612'>💰</tg-emoji> جنيه {amount:.2f}\n<tg-emoji emoji-id='5161427856491807309'>💳</tg-emoji> {method_name}\n<tg-emoji emoji-id='5859518547859869809'>📞</tg-emoji> {account}"
            )
        except:
            pass
    await edit_msg(q, 
        "<tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji> <b>تم إرسال طلب السحب بنجاح!</b>\nسيتم المراجعة خلال 24 ساعة.",
        parse_mode="HTML", reply_markup=back_kb("main")
    )


# ═══════════════════════════════════════════════════════════════
#  █████╗ ██████╗ ███╗   ███╗██╗███╗   ██╗
# ██╔══██╗██╔══██╗████╗ ████║██║████╗  ██║
# ███████║██║  ██║██╔████╔██║██║██╔██╗ ██║
# ██╔══██║██║  ██║██║╚██╔╝██║██║██║╚██╗██║
# ██║  ██║██████╔╝██║ ╚═╝ ██║██║██║ ╚████║
# ╚═╝  ╚═╝╚═════╝ ╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝
# ═══════════════════════════════════════════════════════════════

async def cmd_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await _send_admin_panel(update, ctx)


async def _send_admin_panel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    stats = await db.get_stats()
    text = (
        f"<tg-emoji emoji-id='5114039184507536021'>👑</tg-emoji> <b>لوحة تحكم الأدمن</b>\n\n"
        f"<tg-emoji emoji-id='5012839657545663163'>👥</tg-emoji> المستخدمين: <b>{stats['total']}<b>  |  <tg-emoji emoji-id='5890711263243147926'>🆕</tg-emoji> اليوم: </b>{stats['new_24h']}</b>\n"
        f"🟢 نشطون 24h: <b>{stats['active_24h']}<b>  |  <tg-emoji emoji-id='5370715282044100355'>⭐</tg-emoji> VIP: </b>{stats['vip']}</b>\n"
        f"<tg-emoji emoji-id='4956337889593000947'>🚫</tg-emoji> محظورون: <b>{stats['banned']}<b>  |  <tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji> مهام: </b>{stats['active_tasks']}</b>\n"
        f"<tg-emoji emoji-id='5992452437120652643'>⏳</tg-emoji> سحوبات معلقة: <b>{stats['pending_withdrawals']}</b>\n"
        f"<tg-emoji emoji-id='4958926882994127612'>💰</tg-emoji> رصيد المستخدمين: <b>{fmt_balance(stats['balance_sum'])} جنيه</b>\n"
        f"<tg-emoji emoji-id='5433983375834624526'>💸</tg-emoji> إجمالي السحب: <b>{fmt_balance(stats['total_withdrawn'])} جنيه</b>\n"
        f"<tg-emoji emoji-id='5918112256943459927'>📊</tg-emoji> مهام منجزة: <b>{stats['tasks_done']}</b>"
    )
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("إدارة المهام", callback_data="adm_tasks", api_kwargs={"icon_custom_emoji_id": "5974587361739151285", "style": "success"}),
            InlineKeyboardButton("الاشتراك الإجباري", callback_data="adm_force", api_kwargs={"icon_custom_emoji_id": "6039731759237567238", "style": "primary"}),
        ],
        [
            InlineKeyboardButton("إدارة المستخدمين", callback_data="adm_users", api_kwargs={"icon_custom_emoji_id": "5012839657545663163", "style": "primary"}),
            InlineKeyboardButton("إدارة السحوبات", callback_data="adm_withdrawals", api_kwargs={"icon_custom_emoji_id": "5433983375834624526", "style": "primary"}),
        ],
        [
            InlineKeyboardButton("رسالة جماعية", callback_data="adm_broadcast", api_kwargs={"icon_custom_emoji_id": "6039731759237567238", "style": "primary"}),
            InlineKeyboardButton("أكواد ترويجية", callback_data="adm_promos", api_kwargs={"icon_custom_emoji_id": "5159203583123522328", "style": "primary"}),
        ],
        [
            InlineKeyboardButton("الإعدادات", callback_data="adm_settings", api_kwargs={"icon_custom_emoji_id": "5859588916604047101", "style": "primary"}),
            InlineKeyboardButton("إحصائيات", callback_data="adm_stats", api_kwargs={"icon_custom_emoji_id": "5918112256943459927", "style": "primary"}),
        ],
        [
            InlineKeyboardButton("إدارة VIP", callback_data="adm_vip", api_kwargs={"icon_custom_emoji_id": "5370715282044100355", "style": "primary"}),
            InlineKeyboardButton("📥 تصدير CSV", callback_data="adm_export", api_kwargs={"style": "primary"}),
        ],
        [InlineKeyboardButton("رجوع للبوت", callback_data="main", api_kwargs={"icon_custom_emoji_id": "5197708768091061888", "style": "primary"})],
    ])
    if hasattr(update, "callback_query") and update.callback_query:
        await edit_msg(update.callback_query, text, parse_mode="HTML", reply_markup=kb)
    else:
        await reply_photo(update, text, reply_markup=kb)


# ─────────────────────────── ADMIN: TASKS ───────────────────────────

async def adm_tasks(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    tasks = await db.get_tasks(active_only=False)
    text = f"<tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji> <b>إدارة المهام</b> ({len(tasks)} مهمة)\n\n"
    kb = [[InlineKeyboardButton("إضافة مهمة", callback_data="adm_add_task", api_kwargs={"icon_custom_emoji_id": "5974587361739151285", "style": "primary"})]]
    for t in tasks:
        icon = "<tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji>" if t["is_active"] else "⏸️"
        priv = "<tg-emoji emoji-id='4902389625726698210'>🔒</tg-emoji>" if t.get("is_private") else ""
        kb.append([InlineKeyboardButton(
            f"{icon}{priv} {t['title']} ({t['reward']} ج) — {t['completions']} مرة",
            callback_data=f"adm_task_{t['task_id']}"
        )])
    kb.append([InlineKeyboardButton("رجوع", callback_data="adm_main", api_kwargs={"icon_custom_emoji_id": "5845688877720806733", "style": "danger"})])
    await edit_msg(q, text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))


async def adm_add_task(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    ctx.user_data["admin_state"] = "add_task"
    text = (
        "➕ <b>إضافة مهمة جديدة</b>\n\n"
        "أرسل بيانات المهمة على عدة أسطر:\n\n"
        "``<code>\nالعنوان\nالوصف\nالمكافأة\nرابط القناة\nID القناة\n</code>``\n\n"
        "للقناة الخاصة أضف سطر 6:\n"
        "``<code>private رابط_الدعوة</code>``\n\n"
        "مثال قناة عامة:\n"
        "``<code>\nاشترك في قناتنا\nمحتوى حصري يومياً\n2.5\nhttps://t.me/myChannel\n@myChannel\n</code>``\n\n"
        "مثال قناة خاصة:\n"
        "``<code>\nانضم للجروب الخاص\nجروب VIP حصري\n5\nhttps://t.me/+xxxxx\n-100123456789\nprivate https://t.me/+xxxxx\n</code>``"
    )
    await edit_msg(q, text, parse_mode="HTML",
                               reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("إلغاء", callback_data="adm_tasks", api_kwargs={"icon_custom_emoji_id": "5845688877720806733", "style": "danger"})]]))


async def adm_task_detail(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    tid = int(q.data.split("_")[2])
    task = await db.get_task(tid)
    if not task:
        return
    icon = "<tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji> نشطة" if task["is_active"] else "⏸️ معطلة"
    priv = "<tg-emoji emoji-id='4902389625726698210'>🔒</tg-emoji> خاصة" if task["is_private"] else "🌐 عامة"
    text = (
        f"<tg-emoji emoji-id='5197269100878907942'>📋</tg-emoji> <b>{task['title']}</b>\n\n"
        f"<tg-emoji emoji-id='5861505966666695398'>📝</tg-emoji> {task['description']}\n"
        f"<tg-emoji emoji-id='4958926882994127612'>💰</tg-emoji> المكافأة: {task['reward']} جنيه\n"
        f"🔗 الرابط: {task['channel_link'] or 'لا يوجد'}\n"
        f"🆔 ID: {task['channel_id'] or 'لا يوجد'}\n"
        f"<tg-emoji emoji-id='5918112256943459927'>📊</tg-emoji> الحالة: {icon} | {priv}\n"
        f"<tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji> الإنجازات: {task['completions']} مرة"
    )
    kb = [
        [
            InlineKeyboardButton("حذف", callback_data=f"adm_del_task_{tid}", api_kwargs={"icon_custom_emoji_id": "6003395021653414488", "style": "primary"}),
            InlineKeyboardButton("تعطيل/تفعيل", callback_data=f"adm_toggle_task_{tid}", api_kwargs={"icon_custom_emoji_id": "5854847234054558104", "style": "primary"}),
        ],
        [InlineKeyboardButton("رجوع", callback_data="adm_tasks", api_kwargs={"icon_custom_emoji_id": "5845688877720806733", "style": "danger"})],
    ]
    await edit_msg(q, text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))


async def adm_del_task(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    tid = int(q.data.split("_")[3])
    await db.delete_task(tid)
    await q.answer("✅ تم حذف المهمة!", show_alert=True)
    await adm_tasks(update, ctx)


async def adm_toggle_task(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    tid = int(q.data.split("_")[3])
    await db.toggle_task(tid)
    await q.answer("✅ تم تغيير حالة المهمة!", show_alert=True)
    await adm_tasks(update, ctx)


# ─────────────────────────── ADMIN: FORCE CHANNELS ───────────────────────────

async def adm_force(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    channels = await db.get("force_channels")
    text = f"<tg-emoji emoji-id='6039731759237567238'>📢</tg-emoji> <b>الاشتراك الإجباري</b> ({len(channels)} قناة)\n\nالمستخدم لا يستطيع استخدام البوت إلا بعد الاشتراك في هذه القنوات:\n\n"
    for ch in channels:
        priv = "<tg-emoji emoji-id='4902389625726698210'>🔒</tg-emoji>" if ch.get("is_private") else "🌐"
        text += f"{priv} <b>{ch['name']}</b> — `{ch['id']}`\n"
    kb = [
        [InlineKeyboardButton("إضافة قناة إجبارية", callback_data="adm_add_force", api_kwargs={"icon_custom_emoji_id": "5974587361739151285", "style": "primary"})],
    ]
    for ch in channels:
        kb.append([InlineKeyboardButton(f"حذف: {ch['name']}", callback_data=f"adm_del_force_{ch['id']}", api_kwargs={"icon_custom_emoji_id": "6003395021653414488"})])
    kb.append([InlineKeyboardButton("رجوع", callback_data="adm_main", api_kwargs={"icon_custom_emoji_id": "5845688877720806733", "style": "danger"})])
    await edit_msg(q, text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))


async def adm_add_force(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    ctx.user_data["admin_state"] = "add_force_channel"
    text = (
        "<tg-emoji emoji-id='6039731759237567238'>📢</tg-emoji> <b>إضافة قناة اشتراك إجباري</b>\n\n"
        "أرسل بيانات القناة على عدة أسطر:\n\n"
        "للقناة العامة:\n"
        "``<code>\nاسم القناة\nhttps://t.me/channel\n@channel_id\n</code>``\n\n"
        "للقناة الخاصة:\n"
        "``<code>\nاسم القناة\nhttps://t.me/+xxxxx\n-100123456789\nprivate\n</code>``"
    )
    await edit_msg(q, text, parse_mode="HTML",
                               reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("إلغاء", callback_data="adm_force", api_kwargs={"icon_custom_emoji_id": "5845688877720806733", "style": "danger"})]]))


async def adm_del_force(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    channel_id = q.data.replace("adm_del_force_", "")
    await db.remove_force_channel(channel_id)
    await q.answer("✅ تم حذف القناة من الاشتراك الإجباري!", show_alert=True)
    await adm_force(update, ctx)


# ─────────────────────────── ADMIN: USERS ───────────────────────────

async def adm_users(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    kb = [
        [InlineKeyboardButton("بحث بالـ ID", callback_data="adm_search_user", api_kwargs={"icon_custom_emoji_id": "5861505966666695398", "style": "primary"})],
        [InlineKeyboardButton("آخر 10 مستخدمين", callback_data="adm_recent_users", api_kwargs={"icon_custom_emoji_id": "5197269100878907942", "style": "primary"})],
        [InlineKeyboardButton("أكثر الكاسبين", callback_data="adm_top_earners", api_kwargs={"icon_custom_emoji_id": "5433613063754363635", "style": "primary"})],
        [InlineKeyboardButton("الأكثر دعوة", callback_data="adm_top_referrers", api_kwargs={"icon_custom_emoji_id": "5855190238732751076", "style": "primary"})],
        [InlineKeyboardButton("رجوع", callback_data="adm_main", api_kwargs={"icon_custom_emoji_id": "5845688877720806733", "style": "danger"})],
    ]
    await edit_msg(q, "<tg-emoji emoji-id='5012839657545663163'>👥</tg-emoji> <b>إدارة المستخدمين</b>", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))


async def adm_search_user(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    ctx.user_data["admin_state"] = "search_user"
    await edit_msg(q, "🔍 أرسل ID المستخدم:",
                               reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="adm_users", api_kwargs={"icon_custom_emoji_id": "5845688877720806733", "style": "danger"})]]))


async def adm_recent_users(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute("SELECT * FROM users ORDER BY join_date DESC LIMIT 10")
        users = [dict(r) for r in await cur.fetchall()]
    text = "<tg-emoji emoji-id='5197269100878907942'>📋</tg-emoji> <b>آخر 10 مستخدمين</b>\n\n"
    kb = []
    for u in users:
        kb.append([InlineKeyboardButton(
            f"👤 {u['full_name'][:20]} — {fmt_balance(u['balance'])} ج",
            callback_data=f"adm_user_{u['user_id']}"
        )])
    kb.append([InlineKeyboardButton("رجوع", callback_data="adm_users", api_kwargs={"icon_custom_emoji_id": "5845688877720806733", "style": "danger"})])
    await edit_msg(q, text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))


async def adm_top_earners(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    leaders = await db.get_leaderboard(10)
    text = "<tg-emoji emoji-id='5433613063754363635'>🏆</tg-emoji> <b>أكثر الكاسبين</b>\n\n"
    kb = []
    for u in leaders:
        text += f"<tg-emoji emoji-id='4958926882994127612'>💰</tg-emoji> {u['full_name'][:15]}: {fmt_balance(u['total_earned'])} ج\n"
        kb.append([InlineKeyboardButton(
            f"{u['full_name'][:20]}", callback_data=f"adm_user_{u['user_id']}"
        )])
    kb.append([InlineKeyboardButton("رجوع", callback_data="adm_users", api_kwargs={"icon_custom_emoji_id": "5845688877720806733", "style": "danger"})])
    await edit_msg(q, text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))


async def adm_top_referrers(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute("SELECT * FROM users ORDER BY ref_count DESC LIMIT 10")
        users = [dict(r) for r in await cur.fetchall()]
    text = "<tg-emoji emoji-id='5931746304207100511'>🔗</tg-emoji> <b>أكثر الداعين</b>\n\n"
    kb = []
    for u in users:
        text += f"<tg-emoji emoji-id='5931746304207100511'>🔗</tg-emoji> {u['full_name'][:15]}: {u['ref_count']} دعوة\n"
        kb.append([InlineKeyboardButton(u['full_name'][:20], callback_data=f"adm_user_{u['user_id']}")])
    kb.append([InlineKeyboardButton("رجوع", callback_data="adm_users", api_kwargs={"icon_custom_emoji_id": "5845688877720806733", "style": "danger"})])
    await edit_msg(q, text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))


async def adm_user_detail(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = int(q.data.split("_")[2])
    u = await db.get_user(uid)
    if not u:
        await q.answer("غير موجود!", show_alert=True)
        return
    lv, _ = level_info(u["total_earned"])
    text = (
        f"<tg-emoji emoji-id='5012839657545663163'>👤</tg-emoji> <b>{u['full_name']}</b>\n\n"
        f"<tg-emoji emoji-id='5794357309794686314'>🆔</tg-emoji> ID: `{u['user_id']}`\n"
        f"📱 @{u['username'] or 'لا يوجد'}\n"
        f"<tg-emoji emoji-id='4958926882994127612'>💰</tg-emoji> الرصيد: <b>جنيه {u['balance']:.2f}</b>\n"
        f"<tg-emoji emoji-id='5918243322165465038'>📈</tg-emoji> الأرباح: {fmt_balance(u['total_earned'])} جنيه\n"
        f"<tg-emoji emoji-id='5433983375834624526'>💸</tg-emoji> السحب: {fmt_balance(u['total_withdrawn'])} جنيه\n"
        f"<tg-emoji emoji-id='5931746304207100511'>🔗</tg-emoji> الدعوات: {u['ref_count']} | L2: {u['ref_l2_count']}\n"
        f"<tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji> المهام: {u['tasks_done']}\n"
        f"<tg-emoji emoji-id='5440539497383087970'>🏅</tg-emoji> المستوى: {lv['name']}\n"
        f"<tg-emoji emoji-id='5855190238732751076'>🔥</tg-emoji> الاتساق: {u['streak']} يوم\n"
        f"⭐ VIP: {'نعم ✅' if u['is_vip'] else 'لا'}\n"
        f"🚫 محظور: {'نعم' if u['is_banned'] else 'لا'}\n"
        f"📝 ملاحظات: {u['notes'] or 'لا يوجد'}\n"
        f"<tg-emoji emoji-id='5274055917766202507'>📅</tg-emoji> التسجيل: {(u['join_date'] or '')[:10]}"
    )
    kb = [
        [
            InlineKeyboardButton("💰 تعديل الرصيد", callback_data=f"adm_edit_bal_{uid}", api_kwargs={"style": "primary"}),
            InlineKeyboardButton("📝 ملاحظة", callback_data=f"adm_note_{uid}", api_kwargs={"style": "primary"}),
        ],
        [
            InlineKeyboardButton("حظر" if not u["is_banned"] else "فك الحظر",
                                 callback_data=f"adm_ban_{uid}" if not u["is_banned"] else f"adm_unban_{uid}",
                                 api_kwargs={"icon_custom_emoji_id": "4956337889593000947" if not u["is_banned"] else "5974587361739151285", "style": "danger"}),
            InlineKeyboardButton("VIP 30 يوم" if not u["is_vip"] else "إزالة VIP",
                                 callback_data=f"adm_vip_add_{uid}" if not u["is_vip"] else f"adm_vip_rm_{uid}",
                                 api_kwargs={"icon_custom_emoji_id": "5370715282044100355" if not u["is_vip"] else "4958526153955476488", "style": "success"}),
        ],
        [InlineKeyboardButton("رجوع", callback_data="adm_users", api_kwargs={"icon_custom_emoji_id": "5845688877720806733", "style": "danger"})],
    ]
    await edit_msg(q, text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))


async def adm_ban_user(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = int(q.data.split("_")[2])
    await db.ban(uid, "حظر من الأدمن")
    try:
        await bot_send_photo(ctx.bot, uid, "<tg-emoji emoji-id='4956337889593000947'>🚫</tg-emoji> تم حظر حسابك من قِبل الإدارة.")
    except:
        pass
    await q.answer("✅ تم الحظر!", show_alert=True)
    q.data = f"adm_user_{uid}"
    await adm_user_detail(update, ctx)


async def adm_unban_user(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = int(q.data.split("_")[2])
    await db.unban(uid)
    try:
        await bot_send_photo(ctx.bot, uid, "<tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji> تم رفع الحظر عن حسابك!")
    except:
        pass
    await q.answer("✅ تم رفع الحظر!", show_alert=True)
    q.data = f"adm_user_{uid}"
    await adm_user_detail(update, ctx)


async def adm_edit_balance(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = int(q.data.split("_")[3])
    ctx.user_data["admin_state"] = "edit_balance"
    ctx.user_data["edit_balance_uid"] = uid
    await edit_msg(q, 
        f"<tg-emoji emoji-id='4958926882994127612'>💰</tg-emoji> أرسل المبلغ لتعديل رصيد `{uid}`\nمثال: +50 أو -10",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("إلغاء", callback_data=f"adm_user_{uid}", api_kwargs={"icon_custom_emoji_id": "5845688877720806733", "style": "danger"})]]))


async def adm_add_note(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = int(q.data.split("_")[2])
    ctx.user_data["admin_state"] = "add_note"
    ctx.user_data["note_uid"] = uid
    await edit_msg(q, 
        "<tg-emoji emoji-id='5861505966666695398'>📝</tg-emoji> أرسل الملاحظة:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("إلغاء", callback_data=f"adm_user_{uid}", api_kwargs={"icon_custom_emoji_id": "5845688877720806733", "style": "danger"})]]))


async def adm_vip_add(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = int(q.data.split("_")[3])
    await db.set_vip(uid, 30)
    try:
        await bot_send_photo(ctx.bot, uid, "<tg-emoji emoji-id='5370715282044100355'>⭐</tg-emoji> <b>تهانيك! تمت ترقيتك إلى VIP لمدة 30 يوم!</b>\nاستمتع بمكافآت مضاعفة!")
    except:
        pass
    await q.answer("✅ تم إضافة VIP!", show_alert=True)
    q.data = f"adm_user_{uid}"
    await adm_user_detail(update, ctx)


async def adm_vip_rm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = int(q.data.split("_")[3])
    await db.remove_vip(uid)
    await q.answer("❌ تم إزالة VIP!", show_alert=True)
    q.data = f"adm_user_{uid}"
    await adm_user_detail(update, ctx)


# ─────────────────────────── ADMIN: WITHDRAWALS ───────────────────────────

async def adm_withdrawals(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    pending = await db.get_pending_withdrawals()
    if not pending:
        await edit_msg(q, "<tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji> لا توجد طلبات سحب معلقة!",
                                   reply_markup=back_kb("adm_main"))
        return
    text = f"<tg-emoji emoji-id='5433983375834624526'>💸</tg-emoji> <b>طلبات السحب المعلقة</b> ({len(pending)})\n\n"
    kb = []
    for w in pending:
        name = (w.get("full_name") or "مجهول")[:15]
        method = WITHDRAW_METHODS.get(w["method"], (w["method"], None))[0]
        kb.append([InlineKeyboardButton(
            f"💸 {name} — {fmt_balance(w['amount'])} ج — {method}",
            callback_data=f"adm_w_{w['id']}"
        )])
    kb.append([InlineKeyboardButton("رجوع", callback_data="adm_main", api_kwargs={"icon_custom_emoji_id": "5845688877720806733", "style": "danger"})])
    await edit_msg(q, text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))


async def adm_w_detail(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    wid = int(q.data.split("_")[2])
    w = await db.get_withdrawal(wid)
    u = await db.get_user(w["user_id"])
    method = WITHDRAW_METHODS.get(w["method"], (w["method"], None))[0]
    text = (
        f"<tg-emoji emoji-id='5433983375834624526'>💸</tg-emoji> <b>تفاصيل طلب السحب #{wid}</b>\n\n"
        f"👤 المستخدم: {u['full_name'] if u else '؟'}\n"
        f"<tg-emoji emoji-id='5794357309794686314'>🆔</tg-emoji> ID: `{w['user_id']}`\n"
        f"<tg-emoji emoji-id='4958926882994127612'>💰</tg-emoji> المبلغ: <b>{fmt_balance(w['amount'])} جنيه</b>\n"
        f"<tg-emoji emoji-id='5161427856491807309'>💳</tg-emoji> الطريقة: {method}\n"
        f"<tg-emoji emoji-id='5859518547859869809'>📞</tg-emoji> الحساب: `{w['account_info']}`\n"
        f"<tg-emoji emoji-id='5274055917766202507'>📅</tg-emoji> التاريخ: {w['created_at'][:16]}"
    )
    kb = [
        [
            InlineKeyboardButton("قبول", callback_data=f"adm_w_approve_{wid}", api_kwargs={"icon_custom_emoji_id": "5974587361739151285", "style": "success"}),
            InlineKeyboardButton("رفض", callback_data=f"adm_w_reject_{wid}", api_kwargs={"icon_custom_emoji_id": "4958526153955476488", "style": "danger"}),
        ],
        [InlineKeyboardButton("رجوع", callback_data="adm_withdrawals", api_kwargs={"icon_custom_emoji_id": "5845688877720806733", "style": "danger"})],
    ]
    await edit_msg(q, text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))


async def adm_w_approve(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    wid = int(q.data.split("_")[3])
    w = await db.get_withdrawal(wid)
    await db.process_withdrawal(wid, "approved", "تم التحويل <tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji>")
    if w:
        method = WITHDRAW_METHODS.get(w["method"], (w["method"], None))[0]
        try:
            await bot_send_photo(ctx.bot, w["user_id"],
                f"<tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji><tg-emoji emoji-id='4956596167451346576'>🎉</tg-emoji> <b>تم قبول طلب سحبك!</b>\n\n"
                f"╔══════════════════╗\n"
                f"║  <tg-emoji emoji-id='4958926882994127612'>💰</tg-emoji> <b>جنيه {w['amount']:.2f}</b>\n"
                f"║  <tg-emoji emoji-id='5161427856491807309'>💳</tg-emoji> {method}\n"
                f"╚══════════════════╝\n\n"
                f"سيصلك خلال دقائق! <tg-emoji emoji-id='5861568308116984245'>🚀</tg-emoji>\n\n"
                f"<tg-emoji emoji-id='5434045652860416220'>💡</tg-emoji> <b>شارك البوت مع أصدقاءك واكسب أكثر!</b>"
            )
        except:
            pass
    await q.answer("✅ تم قبول الطلب!", show_alert=True)
    await adm_withdrawals(update, ctx)


async def adm_w_reject(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    wid = int(q.data.split("_")[3])
    w = await db.get_withdrawal(wid)
    await db.process_withdrawal(wid, "rejected", "مرفوض <tg-emoji emoji-id='4958526153955476488'>❌</tg-emoji>")
    if w:
        try:
            await bot_send_photo(ctx.bot, w["user_id"],
                f"<tg-emoji emoji-id='4958526153955476488'>❌</tg-emoji> <b>تم رفض طلب سحبك</b>\n<tg-emoji emoji-id='4958926882994127612'>💰</tg-emoji> تم إعادة جنيه {w['amount']:.2f} لرصيدك."
            )
        except:
            pass
    await q.answer("❌ تم الرفض وإعادة الرصيد!", show_alert=True)
    await adm_withdrawals(update, ctx)


# ─────────────────────────── ADMIN: BROADCAST ───────────────────────────

async def adm_broadcast(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    kb = [
        [InlineKeyboardButton("إرسال للكل", callback_data="adm_bc_all", api_kwargs={"icon_custom_emoji_id": "6039731759237567238", "style": "primary"})],
        [InlineKeyboardButton("🟢 النشطون (7 أيام)", callback_data="adm_bc_active", api_kwargs={"style": "primary"})],
        [InlineKeyboardButton("VIP فقط", callback_data="adm_bc_vip", api_kwargs={"icon_custom_emoji_id": "5370715282044100355", "style": "primary"})],
        [InlineKeyboardButton("رجوع", callback_data="adm_main", api_kwargs={"icon_custom_emoji_id": "5845688877720806733", "style": "danger"})],
    ]
    await edit_msg(q, "<tg-emoji emoji-id='6039731759237567238'>📢</tg-emoji> <b>إرسال رسالة جماعية</b>\nاختر الفئة:", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))


async def adm_bc_select(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    target = q.data.split("_")[2]
    ctx.user_data["admin_state"] = f"broadcast_{target}"
    await edit_msg(q, 
        "<tg-emoji emoji-id='6039731759237567238'>📢</tg-emoji> أرسل الرسالة:\n<b>(يمكنك استخدام Markdown)</b>",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("إلغاء", callback_data="adm_broadcast", api_kwargs={"icon_custom_emoji_id": "5845688877720806733", "style": "danger"})]]))


# ─────────────────────────── ADMIN: PROMO CODES ───────────────────────────

async def adm_promos(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    promos = await db.get_promos()
    text = f"<tg-emoji emoji-id='5159203583123522328'>🎟️</tg-emoji> <b>الأكواد الترويجية</b> ({len(promos)} كود)\n\n"
    kb = [[InlineKeyboardButton("إنشاء كود جديد", callback_data="adm_add_promo", api_kwargs={"icon_custom_emoji_id": "5974587361739151285", "style": "primary"})]]
    for p in promos:
        status = "<tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji>" if p["is_active"] else "<tg-emoji emoji-id='4958526153955476488'>❌</tg-emoji>"
        text += f"{status} `{p['code']}` — {p['reward']} ج — {p['used_count']}/{p['max_uses']}\n"
    kb.append([InlineKeyboardButton("رجوع", callback_data="adm_main", api_kwargs={"icon_custom_emoji_id": "5845688877720806733", "style": "danger"})])
    await edit_msg(q, text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))


async def adm_add_promo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    ctx.user_data["admin_state"] = "add_promo"
    text = (
        "<tg-emoji emoji-id='5159203583123522328'>🎟️</tg-emoji> <b>إنشاء كود ترويجي</b>\n\n"
        "أرسل بيانات الكود:\n\n"
        "``<code>\nاسم_الكود\nالمكافأة\nعدد_الاستخدامات\n</code>``\n\n"
        "مثال:\n``<code>\nEID2025\n5\n200\n</code>``\n\n"
        "أو أرسل AUTO لتوليد كود عشوائي:\n``<code>\nAUTO\n3\n50\n</code>``"
    )
    await edit_msg(q, text, parse_mode="HTML",
                               reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("إلغاء", callback_data="adm_promos", api_kwargs={"icon_custom_emoji_id": "5845688877720806733", "style": "danger"})]]))


# ─────────────────────────── ADMIN: SETTINGS ───────────────────────────

async def adm_settings(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    s = await db.all_settings()
    maint = "<tg-emoji emoji-id='5765711271444965470'>🔴</tg-emoji> مفعّل" if s.get("maintenance_mode") else "🟢 معطّل"
    text = (
        f"<tg-emoji emoji-id='5859588916604047101'>⚙️</tg-emoji> <b>إعدادات البوت</b>\n\n"
        f"<tg-emoji emoji-id='5931746304207100511'>🔗</tg-emoji> مكافأة الدعوة L1: <b>{s.get('referral_reward_l1')} جنيه</b>\n"
        f"<tg-emoji emoji-id='5931746304207100511'>🔗</tg-emoji> مكافأة الدعوة L2: <b>{s.get('referral_reward_l2')} جنيه</b>\n"
        f"<tg-emoji emoji-id='5931746304207100511'>🔗</tg-emoji> مكافأة الدعوة L3: <b>{s.get('referral_reward_l3')} جنيه</b>\n"
        f"<tg-emoji emoji-id='5970074171449808121'>🎁</tg-emoji> الهدية اليومية: <b>{s.get('daily_gift_min')} - {s.get('daily_gift_max')} جنيه</b>\n"
        f"<tg-emoji emoji-id='5433983375834624526'>💸</tg-emoji> حد السحب: <b>{s.get('min_withdraw')} جنيه</b>\n"
        f"<tg-emoji emoji-id='5370715282044100355'>⭐</tg-emoji> مضاعف VIP: <b>x{s.get('vip_multiplier')}</b>\n"
        f"<tg-emoji emoji-id='5274055917766202507'>📅</tg-emoji> هدف التحدي الأسبوعي: <b>{s.get('weekly_challenge_tasks')} مهام</b>\n"
        f"<tg-emoji emoji-id='5433613063754363635'>🏆</tg-emoji> مكافأة التحدي: <b>{s.get('weekly_challenge_reward')} جنيه</b>\n"
        f"<tg-emoji emoji-id='5855065341083784332'>🔧</tg-emoji> الصيانة: <b>{maint}</b>\n"
        f"💱 سعر الدولار: <b>{s.get('usd_to_egp', 50)} جنيه</b>\n"
        f"<tg-emoji emoji-id='5814263327865444782'>🎰</tg-emoji> سقف جائزة العجلة: <b>{s.get('wheel_max_prize', 2.0)} جنيه</b>"
    )
    kb = [
        [InlineKeyboardButton("مكافأة الدعوة", callback_data="adm_set_ref", api_kwargs={"icon_custom_emoji_id": "5931746304207100511", "style": "primary"}),
         InlineKeyboardButton("حد السحب", callback_data="adm_set_withdraw", api_kwargs={"icon_custom_emoji_id": "5433983375834624526", "style": "primary"})],
        [InlineKeyboardButton("الهدية اليومية", callback_data="adm_set_gift", api_kwargs={"icon_custom_emoji_id": "5970074171449808121", "style": "primary"}),
         InlineKeyboardButton("مضاعف VIP", callback_data="adm_set_vip_mult", api_kwargs={"icon_custom_emoji_id": "5370715282044100355", "style": "primary"})],
        [InlineKeyboardButton("التحدي الأسبوعي", callback_data="adm_set_weekly", api_kwargs={"icon_custom_emoji_id": "5274055917766202507", "style": "primary"}),
         InlineKeyboardButton("مكافأة الاتساق", callback_data="adm_set_streak", api_kwargs={"icon_custom_emoji_id": "5855190238732751076", "style": "primary"})],
        [InlineKeyboardButton("جوائز العجلة", callback_data="adm_set_wheel", api_kwargs={"icon_custom_emoji_id": "5814263327865444782", "style": "primary"}),
         InlineKeyboardButton("مكافأة الترحيب", callback_data="adm_set_welcome", api_kwargs={"icon_custom_emoji_id": "4958926882994127612", "style": "primary"})],
        [InlineKeyboardButton("💱 سعر الدولار بالجنيه", callback_data="adm_set_usd_rate", api_kwargs={"style": "primary"}),
         InlineKeyboardButton("🎰 سقف جائزة العجلة", callback_data="adm_set_wheel_max", api_kwargs={"style": "primary"})],
        [InlineKeyboardButton(
            "إيقاف الصيانة" if s.get("maintenance_mode") else "تفعيل الصيانة",
            callback_data="adm_toggle_maint",
            api_kwargs={"icon_custom_emoji_id": "5855065341083784332", "style": "danger" if not s.get("maintenance_mode") else "success"}
        )],
        [InlineKeyboardButton("رجوع", callback_data="adm_main", api_kwargs={"icon_custom_emoji_id": "5845688877720806733", "style": "danger"})],
    ]
    await edit_msg(q, text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))


async def adm_setting_prompt(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    key = q.data.replace("adm_set_", "")
    prompts = {
        "ref":      ("set_ref_reward",    "🔗 أرسل قيمة مكافأة الدعوة L1 L2 L3 (أرقام مفصولة بمسافة):\nمثال: 2 0.5 0.25"),
        "withdraw": ("set_min_withdraw",  "💸 أرسل الحد الأدنى للسحب:\nمثال: 10"),
        "gift":     ("set_gift_range",    "🎁 أرسل نطاق الهدية (min max):\nمثال: 0.5 3"),
        "vip_mult": ("set_vip_mult",      "⭐ أرسل مضاعف VIP:\nمثال: 2.5"),
        "weekly":   ("set_weekly",        "📅 أرسل هدف التحدي ومكافأته:\nمثال: 5 10"),
        "streak":   ("set_streak",        "🔥 أرسل مكافأة كل يوم اتساق:\nمثال: 0.5"),
        "wheel":    ("set_wheel_prizes",  "🎰 أرسل جوائز العجلة مفصولة بمسافة:\nمثال: 0.1 0.25 0.5 1 2 3 5"),
        "welcome":  ("set_welcome_bonus", "💰 أرسل مكافأة الترحيب:\nمثال: 1.5"),
        "usd_rate":  ("set_usd_rate",      "💱 أرسل سعر الدولار بالجنيه المصري:\nمثال: 50.5"),
        "wheel_max": ("set_wheel_max",     "🎰 أرسل أقصى جائزة ممكنة من العجلة بالجنيه:\nمثال: 2"),
    }
    if key not in prompts:
        return
    state, msg = prompts[key]
    ctx.user_data["admin_state"] = state
    await edit_msg(q, msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("إلغاء", callback_data="adm_settings", api_kwargs={"icon_custom_emoji_id": "5845688877720806733", "style": "danger"})]]))


async def adm_toggle_maintenance(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    curr = await db.get("maintenance_mode")
    await db.set("maintenance_mode", not curr)
    status = "مفعّل <tg-emoji emoji-id='5765711271444965470'>🔴</tg-emoji>" if not curr else "معطّل 🟢"
    await q.answer(f"وضع الصيانة: {status}", show_alert=True)
    await adm_settings(update, ctx)


# ─────────────────────────── ADMIN: VIP MANAGEMENT ───────────────────────────

async def adm_vip(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute("SELECT * FROM users WHERE is_vip=1")
        vip_users = [dict(r) for r in await cur.fetchall()]
    text = f"<tg-emoji emoji-id='5370715282044100355'>⭐</tg-emoji> <b>أعضاء VIP</b> ({len(vip_users)})\n\n"
    kb = [[InlineKeyboardButton("إضافة VIP يدوياً", callback_data="adm_add_vip_manual", api_kwargs={"icon_custom_emoji_id": "5974587361739151285", "style": "primary"})]]
    for u in vip_users:
        exp = u.get("vip_expiry", "")[:10] if u.get("vip_expiry") else "غير محدد"
        kb.append([InlineKeyboardButton(
            f"⭐ {u['full_name'][:20]} (حتى {exp})",
            callback_data=f"adm_vip_rm_{u['user_id']}"
        )])
    kb.append([InlineKeyboardButton("رجوع", callback_data="adm_main", api_kwargs={"icon_custom_emoji_id": "5845688877720806733", "style": "danger"})])
    await edit_msg(q, text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))


async def adm_add_vip_manual(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    ctx.user_data["admin_state"] = "add_vip_manual"
    await edit_msg(q, 
        "<tg-emoji emoji-id='5370715282044100355'>⭐</tg-emoji> أرسل ID المستخدم وعدد الأيام:\nمثال: 123456789 30",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("إلغاء", callback_data="adm_vip", api_kwargs={"icon_custom_emoji_id": "5845688877720806733", "style": "danger"})]]))


# ─────────────────────────── ADMIN: STATS ───────────────────────────

async def adm_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    s = await db.get_stats()
    # أرباح هذا الأسبوع
    week_start = (datetime.datetime.now() - datetime.timedelta(days=7)).isoformat()
    async with aiosqlite.connect(DB_PATH) as conn:
        cur = await conn.execute(
            "SELECT COALESCE(SUM(amount),0) FROM transactions WHERE created_at>? AND amount>0",
            (week_start,)
        )
        weekly_earned = (await cur.fetchone())[0]
        cur2 = await conn.execute("SELECT COUNT(*) FROM completed_tasks WHERE completed_at>?", (week_start,))
        weekly_tasks = (await cur2.fetchone())[0]

    text = (
        f"<tg-emoji emoji-id='5918112256943459927'>📊</tg-emoji> <b>إحصائيات شاملة</b>\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"<tg-emoji emoji-id='5012839657545663163'>👥</tg-emoji> المستخدمين\n"
        f"  الإجمالي: <b>{s['total']}</b>\n"
        f"  جديد اليوم: <b>{s['new_24h']}</b>\n"
        f"  نشطون 24h: <b>{s['active_24h']}</b>\n"
        f"  <tg-emoji emoji-id='5370715282044100355'>⭐</tg-emoji> VIP: <b>{s['vip']}</b>\n"
        f"  <tg-emoji emoji-id='4956337889593000947'>🚫</tg-emoji> محظورون: <b>{s['banned']}</b>\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"<tg-emoji emoji-id='4958926882994127612'>💰</tg-emoji> المالية\n"
        f"  أرصدة المستخدمين: <b>{fmt_balance(s['balance_sum'])} ج</b>\n"
        f"  إجمالي السحب: <b>{fmt_balance(s['total_withdrawn'])} ج</b>\n"
        f"  سحوبات معلقة: <b>{s['pending_withdrawals']}</b>\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"<tg-emoji emoji-id='5197269100878907942'>📋</tg-emoji> هذا الأسبوع\n"
        f"  مهام منجزة: <b>{weekly_tasks}</b>\n"
        f"  أرباح موزعة: <b>{fmt_balance(weekly_earned)} ج</b>\n\n"
        f"  <tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji> المهام النشطة: <b>{s['active_tasks']}</b>\n"
        f"  <tg-emoji emoji-id='5918112256943459927'>📊</tg-emoji> إجمالي الإنجازات: <b>{s['tasks_done']}</b>"
    )
    await edit_msg(q, text, parse_mode="HTML", reply_markup=back_kb("adm_main"))


# ─────────────────────────── ADMIN: EXPORT ───────────────────────────

async def adm_export(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer("⏳ جاري التصدير...")
    users = await db.get_all_users(include_banned=True)
    lines = ["ID,الاسم,اليوزر,الرصيد,الأرباح,السحب,الدعوات,المهام,VIP,محظور,تاريخ_التسجيل"]
    for u in users:
        lines.append(
            f"{u['user_id']},{u['full_name']},{u['username'] or ''},"
            f"{fmt_balance(u['balance'])},{fmt_balance(u['total_earned'])},"
            f"{fmt_balance(u['total_withdrawn'])},{u['ref_count']},{u['tasks_done']},"
            f"{'نعم' if u['is_vip'] else 'لا'},{'نعم' if u['is_banned'] else 'لا'},"
            f"{(u['join_date'] or '')[:10]}"
        )
    content = "\n".join(lines).encode("utf-8-sig")
    fname = f"users_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    file_obj = io.BytesIO(content)
    file_obj.name = fname
    await ctx.bot.send_document(q.from_user.id, file_obj, filename=fname,
                                 caption=f"📥 {len(users)} مستخدم")


# ─────────────────────────── ADMIN TEXT INPUTS ───────────────────────────

async def _admin_text_input(update: Update, ctx: ContextTypes.DEFAULT_TYPE, state: str, text: str):
    uid = update.effective_user.id

    async def reply(msg):
        await reply_photo(update, msg)

    ctx.user_data.pop("admin_state", None)

    if state == "add_task":
        lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
        if len(lines) < 5:
            await reply("<tg-emoji emoji-id='4958526153955476488'>❌</tg-emoji> أرسل 5 أسطر على الأقل:\nالعنوان\nالوصف\nالمكافأة\nالرابط\nالـID")
            return
        try:
            title, desc, reward, link, channel_id = lines[:5]
            reward = float(reward)
            is_private = len(lines) > 5 and lines[5].startswith("private")
            invite_link = lines[5].replace("private", "").strip() if is_private else ""
            await db.add_task(title, desc, reward, "subscribe", channel_id, link,
                              title, is_private, invite_link)
            await reply(f"<tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji> تمت إضافة المهمة!\n<b>{title}</b> — {reward} جنيه\n{'🔒 خاصة' if is_private else '🌐 عامة'}")
        except Exception as e:
            await reply(f"<tg-emoji emoji-id='4958526153955476488'>❌</tg-emoji> خطأ: {e}")

    elif state == "add_force_channel":
        lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
        if len(lines) < 3:
            await reply("<tg-emoji emoji-id='4958526153955476488'>❌</tg-emoji> أرسل 3 أسطر:\nالاسم\nالرابط\nالـID")
            return
        name, link, channel_id = lines[:3]
        is_private = len(lines) > 3 and lines[3].lower() == "private"
        invite_link = link if is_private else ""
        await db.add_force_channel(channel_id, link, name, is_private, invite_link)
        await reply(f"<tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji> تمت إضافة القناة الإجبارية!\n<b>{name}</b> {'🔒 خاصة' if is_private else '🌐 عامة'}")

    elif state == "edit_balance":
        try:
            amount = float(text.replace("+", ""))
            target = ctx.user_data.pop("edit_balance_uid")
            await db.add_balance(target, amount, "admin", f"تعديل من الأدمن {uid}")
            u = await db.get_user(target)
            await reply(f"<tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji> تم!\nالرصيد الجديد: <b>{fmt_balance(u['balance'])} جنيه</b>")
            try:
                sign = "+" if amount > 0 else ""
                await bot_send_photo(ctx.bot, target, f"<tg-emoji emoji-id='4958926882994127612'>💰</tg-emoji> تم تعديل رصيدك: {sign}{amount:.2f} جنيه\nالرصيد الجديد: {u['balance']:.2f} جنيه")
            except:
                pass
        except Exception as e:
            await reply(f"<tg-emoji emoji-id='4958526153955476488'>❌</tg-emoji> خطأ: {e}")

    elif state == "add_note":
        target = ctx.user_data.pop("note_uid")
        async with aiosqlite.connect(DB_PATH) as conn:
            await conn.execute("UPDATE users SET notes=? WHERE user_id=?", (text, target))
            await conn.commit()
        await reply("<tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji> تم حفظ الملاحظة!")

    elif state == "search_user":
        try:
            target = int(text)
            u = await db.get_user(target)
            if u:
                await update.message.reply_text(
                    f"<tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji> وُجد: {u['full_name']}",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👤 التفاصيل", callback_data=f"adm_user_{target}", api_kwargs={"style": "primary"}, parse_mode="HTML")]])
                )
            else:
                await reply("<tg-emoji emoji-id='4958526153955476488'>❌</tg-emoji> غير موجود!")
        except:
            await reply("<tg-emoji emoji-id='4958526153955476488'>❌</tg-emoji> أرسل رقم ID فقط")

    elif state.startswith("broadcast_"):
        target = state.replace("broadcast_", "")
        if target == "all":
            users = await db.get_all_users(include_banned=False)
        elif target == "active":
            users = await db.get_active_users(days=7)
        elif target == "vip":
            async with aiosqlite.connect(DB_PATH) as conn:
                conn.row_factory = aiosqlite.Row
                cur = await conn.execute("SELECT * FROM users WHERE is_vip=1 AND is_banned=0")
                users = [dict(r) for r in await cur.fetchall()]
        else:
            users = []
        await update.message.reply_text(f"<tg-emoji emoji-id='6039731759237567238'>📢</tg-emoji> جاري الإرسال لـ <b>{len(users)}</b> مستخدم...", parse_mode="HTML")
        sent = failed = 0
        for u in users:
            try:
                await bot_send_photo(ctx.bot, u["user_id"], text)
                sent += 1
                await asyncio.sleep(0.05)
            except:
                failed += 1
        await reply(f"<tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji> اكتمل!\n<tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji> نجح: {sent}\n<tg-emoji emoji-id='4958526153955476488'>❌</tg-emoji> فشل: {failed}")

    elif state == "add_promo":
        lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
        if len(lines) < 3:
            await reply("<tg-emoji emoji-id='4958526153955476488'>❌</tg-emoji> أرسل 3 أسطر:\nاسم_الكود (أو AUTO)\nالمكافأة\nالاستخدامات")
            return
        code = lines[0]
        if code.upper() == "AUTO":
            code = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
        try:
            reward = float(lines[1])
            max_uses = int(lines[2])
            await db.create_promo(code, reward, max_uses, uid)
            await reply(f"<tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji> تم إنشاء الكود!\n<tg-emoji emoji-id='5159203583123522328'>🎟️</tg-emoji> `{code.upper()}`\n<tg-emoji emoji-id='4958926882994127612'>💰</tg-emoji> {reward} جنيه\n<tg-emoji emoji-id='5012839657545663163'>👥</tg-emoji> {max_uses} استخدام")
        except Exception as e:
            await reply(f"<tg-emoji emoji-id='4958526153955476488'>❌</tg-emoji> خطأ: {e}")

    elif state == "add_vip_manual":
        parts = text.strip().split()
        if len(parts) < 2:
            await reply("<tg-emoji emoji-id='4958526153955476488'>❌</tg-emoji> أرسل: ID عدد_الأيام")
            return
        try:
            target = int(parts[0])
            days = int(parts[1])
            await db.set_vip(target, days)
            await reply(f"<tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji> تم إضافة VIP لـ `{target}` لمدة {days} يوم!")
            try:
                await bot_send_photo(ctx.bot, target, f"<tg-emoji emoji-id='5370715282044100355'>⭐</tg-emoji> تمت ترقيتك لـ VIP لمدة {days} يوم! <tg-emoji emoji-id='4956596167451346576'>🎉</tg-emoji>")
            except:
                pass
        except Exception as e:
            await reply(f"<tg-emoji emoji-id='4958526153955476488'>❌</tg-emoji> خطأ: {e}")

    elif state == "set_ref_reward":
        try:
            parts = text.strip().split()
            await db.set("referral_reward_l1", float(parts[0]))
            if len(parts) > 1:
                await db.set("referral_reward_l2", float(parts[1]))
            if len(parts) > 2:
                await db.set("referral_reward_l3", float(parts[2]))
            await reply(f"<tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji> تم تحديث مكافآت الدعوة!")
        except Exception as e:
            await reply(f"<tg-emoji emoji-id='4958526153955476488'>❌</tg-emoji> خطأ: {e}")

    elif state == "set_min_withdraw":
        try:
            await db.set("min_withdraw", float(text))
            await reply(f"<tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji> تم تغيير حد السحب إلى <b>{text} جنيه</b>")
        except:
            await reply("<tg-emoji emoji-id='4958526153955476488'>❌</tg-emoji> أرسل رقماً صحيحاً")

    elif state == "set_gift_range":
        try:
            parts = text.strip().split()
            await db.set("daily_gift_min", float(parts[0]))
            await db.set("daily_gift_max", float(parts[1]))
            await reply(f"<tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji> الهدية اليومية: <b>{parts[0]} - {parts[1]} جنيه</b>")
        except:
            await reply("<tg-emoji emoji-id='4958526153955476488'>❌</tg-emoji> أرسل: min max")

    elif state == "set_vip_mult":
        try:
            await db.set("vip_multiplier", float(text))
            await reply(f"<tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji> مضاعف VIP: <b>x{text}</b>")
        except:
            await reply("<tg-emoji emoji-id='4958526153955476488'>❌</tg-emoji> رقم خاطئ")

    elif state == "set_weekly":
        try:
            parts = text.strip().split()
            await db.set("weekly_challenge_tasks", int(parts[0]))
            await db.set("weekly_challenge_reward", float(parts[1]))
            await reply(f"<tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji> التحدي الأسبوعي: {parts[0]} مهام = {parts[1]} جنيه")
        except:
            await reply("<tg-emoji emoji-id='4958526153955476488'>❌</tg-emoji> أرسل: عدد_المهام المكافأة")

    elif state == "set_streak":
        try:
            await db.set("streak_bonus", float(text))
            await reply(f"<tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji> مكافأة الاتساق: <b>{text} جنيه</b>/يوم")
        except:
            await reply("<tg-emoji emoji-id='4958526153955476488'>❌</tg-emoji> رقم خاطئ")

    elif state == "set_wheel_prizes":
        try:
            prizes = [float(x) for x in text.strip().split()]
            await db.set("wheel_prizes", prizes)
            await reply(f"<tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji> جوائز العجلة: {prizes}")
        except:
            await reply("<tg-emoji emoji-id='4958526153955476488'>❌</tg-emoji> أرسل أرقاماً مفصولة بمسافات")

    elif state == "set_welcome_bonus":
        try:
            await db.set("welcome_bonus", float(text))
            await reply(f"<tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji> مكافأة الترحيب: <b>{text} جنيه</b>")
        except:
            await reply("<tg-emoji emoji-id='4958526153955476488'>❌</tg-emoji> رقم خاطئ")

    elif state == "set_wheel_max":
        try:
            await db.set("wheel_max_prize", float(text))
            await reply(f"<tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji> سقف جائزة العجلة: <b>{text} جنيه</b>")
        except:
            await reply("<tg-emoji emoji-id='4958526153955476488'>❌</tg-emoji> رقم خاطئ")

    elif state == "set_usd_rate":
        try:
            rate = float(text)
            await db.set("usd_to_egp", rate)
            await reply(f"<tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji> سعر الدولار: <b>{rate} جنيه</b>")
        except:
            await reply("<tg-emoji emoji-id='4958526153955476488'>❌</tg-emoji> رقم خاطئ")


# ═══════════════════════════════════════════════════════════════
#  ██████╗ ███████╗ ██████╗ ██╗███████╗████████╗██████╗  █████╗ ████████╗██╗ ██████╗ ███╗   ██╗
# ██╔══██╗██╔════╝██╔════╝ ██║██╔════╝╚══██╔══╝██╔══██╗██╔══██╗╚══██╔══╝██║██╔═══██╗████╗  ██║
# ██████╔╝█████╗  ██║  ███╗██║███████╗   ██║   ██████╔╝███████║   ██║   ██║██║   ██║██╔██╗ ██║
# ██╔══██╗██╔══╝  ██║   ██║██║╚════██║   ██║   ██╔══██╗██╔══██║   ██║   ██║██║   ██║██║╚██╗██║
# ██║  ██║███████╗╚██████╔╝██║███████║   ██║   ██║  ██║██║  ██║   ██║   ██║╚██████╔╝██║ ╚████║
# ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝
# ═══════════════════════════════════════════════════════════════

async def main():
    await db.init()

    # ── تشغيل Flask API Server في Thread خلفي ──────────────────────
    api_thread = threading.Thread(target=start_api_server, daemon=True, name="FlaskAPI")
    api_thread.start()
    print("✅ API Server شغال على http://0.0.0.0:5000")
    print("   الـ Endpoints:")
    print("   GET /api/health")
    print("   GET /api/user/<id>")
    print("   GET /api/user/<id>/transactions")
    print("   GET /api/leaderboard")
    print("   GET /api/stats")
    print("─" * 50)

    app = Application.builder().token(BOT_TOKEN).build()

    # ── User commands ──
    app.add_handler(CommandHandler("start",       cmd_start))
    app.add_handler(CommandHandler("admin",       cmd_admin))
    app.add_handler(CommandHandler("balance",     lambda u, c: u.message.reply_text(
        f"<tg-emoji emoji-id='4958926882994127612'>💰</tg-emoji> رصيدك: <b>{fmt_balance((lambda x: x['balance'] if x else 0)(asyncio.get_event_loop().run_until_complete(db.get_user(u.effective_user.id))))} جنيه</b>",
        parse_mode="HTML"
    )))

    # ── User callbacks ──
    app.add_handler(CallbackQueryHandler(cb_main,          pattern="^main$"))
    app.add_handler(CallbackQueryHandler(cb_check_force,   pattern="^check_force_sub$"))
    app.add_handler(CallbackQueryHandler(cb_profile,       pattern="^profile$"))
    app.add_handler(CallbackQueryHandler(cb_achievements,  pattern="^achievements$"))
    app.add_handler(CallbackQueryHandler(cb_leaderboard,   pattern="^leaderboard$"))
    app.add_handler(CallbackQueryHandler(cb_vip_info,      pattern="^vip_info$"))
    app.add_handler(CallbackQueryHandler(cb_daily_gift,    pattern="^daily_gift$"))
    app.add_handler(CallbackQueryHandler(cb_wheel,         pattern="^wheel$"))
    app.add_handler(CallbackQueryHandler(cb_spin,          pattern="^spin_wheel$"))
    app.add_handler(CallbackQueryHandler(cb_referral,      pattern="^referral$"))
    app.add_handler(CallbackQueryHandler(cb_withdraw,      pattern="^withdraw$"))
    app.add_handler(CallbackQueryHandler(cb_wmethod,       pattern="^wmethod_"))
    app.add_handler(CallbackQueryHandler(cb_w_confirm,     pattern="^w_confirm$"))
    app.add_handler(CallbackQueryHandler(cb_promo,         pattern="^promo$"))
    app.add_handler(CallbackQueryHandler(cb_weekly,        pattern="^weekly_challenge$"))
    app.add_handler(CallbackQueryHandler(cb_tasks,         pattern="^tasks$"))
    app.add_handler(CallbackQueryHandler(cb_task_view,     pattern="^task_\\d+$"))
    app.add_handler(CallbackQueryHandler(cb_verify,        pattern="^verify_\\d+$"))

    # ── Admin callbacks ──
    app.add_handler(CallbackQueryHandler(_send_admin_panel,    pattern="^adm_main$"))
    app.add_handler(CallbackQueryHandler(adm_tasks,            pattern="^adm_tasks$"))
    app.add_handler(CallbackQueryHandler(adm_add_task,         pattern="^adm_add_task$"))
    app.add_handler(CallbackQueryHandler(adm_task_detail,      pattern="^adm_task_\\d+$"))
    app.add_handler(CallbackQueryHandler(adm_del_task,         pattern="^adm_del_task_\\d+$"))
    app.add_handler(CallbackQueryHandler(adm_toggle_task,      pattern="^adm_toggle_task_\\d+$"))
    app.add_handler(CallbackQueryHandler(adm_force,            pattern="^adm_force$"))
    app.add_handler(CallbackQueryHandler(adm_add_force,        pattern="^adm_add_force$"))
    app.add_handler(CallbackQueryHandler(adm_del_force,        pattern="^adm_del_force_"))
    app.add_handler(CallbackQueryHandler(adm_users,            pattern="^adm_users$"))
    app.add_handler(CallbackQueryHandler(adm_search_user,      pattern="^adm_search_user$"))
    app.add_handler(CallbackQueryHandler(adm_recent_users,     pattern="^adm_recent_users$"))
    app.add_handler(CallbackQueryHandler(adm_top_earners,      pattern="^adm_top_earners$"))
    app.add_handler(CallbackQueryHandler(adm_top_referrers,    pattern="^adm_top_referrers$"))
    app.add_handler(CallbackQueryHandler(adm_user_detail,      pattern="^adm_user_\\d+$"))
    app.add_handler(CallbackQueryHandler(adm_ban_user,         pattern="^adm_ban_\\d+$"))
    app.add_handler(CallbackQueryHandler(adm_unban_user,       pattern="^adm_unban_\\d+$"))
    app.add_handler(CallbackQueryHandler(adm_edit_balance,     pattern="^adm_edit_bal_\\d+$"))
    app.add_handler(CallbackQueryHandler(adm_add_note,         pattern="^adm_note_\\d+$"))
    app.add_handler(CallbackQueryHandler(adm_vip_add,          pattern="^adm_vip_add_\\d+$"))
    app.add_handler(CallbackQueryHandler(adm_vip_rm,           pattern="^adm_vip_rm_\\d+$"))
    app.add_handler(CallbackQueryHandler(adm_withdrawals,      pattern="^adm_withdrawals$"))
    app.add_handler(CallbackQueryHandler(adm_w_detail,         pattern="^adm_w_\\d+$"))
    app.add_handler(CallbackQueryHandler(adm_w_approve,        pattern="^adm_w_approve_\\d+$"))
    app.add_handler(CallbackQueryHandler(adm_w_reject,         pattern="^adm_w_reject_\\d+$"))
    app.add_handler(CallbackQueryHandler(adm_broadcast,        pattern="^adm_broadcast$"))
    app.add_handler(CallbackQueryHandler(adm_bc_select,        pattern="^adm_bc_"))
    app.add_handler(CallbackQueryHandler(adm_promos,           pattern="^adm_promos$"))
    app.add_handler(CallbackQueryHandler(adm_add_promo,        pattern="^adm_add_promo$"))
    app.add_handler(CallbackQueryHandler(adm_settings,         pattern="^adm_settings$"))
    app.add_handler(CallbackQueryHandler(adm_setting_prompt,   pattern="^adm_set_"))
    app.add_handler(CallbackQueryHandler(adm_toggle_maintenance, pattern="^adm_toggle_maint$"))
    app.add_handler(CallbackQueryHandler(adm_vip,              pattern="^adm_vip$"))
    app.add_handler(CallbackQueryHandler(adm_add_vip_manual,   pattern="^adm_add_vip_manual$"))
    app.add_handler(CallbackQueryHandler(adm_stats,            pattern="^adm_stats$"))
    app.add_handler(CallbackQueryHandler(adm_export,           pattern="^adm_export$"))

    # ── Text handler ──
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("<tg-emoji emoji-id='5974587361739151285'>✅</tg-emoji> البوت شغال!")
    await app.run_polling(drop_pending_updates=True)


import asyncio
# لا حاجة لـ nest_asyncio في بيئة الإنتاج الثابتة

async def main():
    # ضع هنا منطق إعداد البوت الخاص بك
    # تأكد من استخدام await عند تشغيل البوت
    # مثال:
    # await application.run_polling()
    pass

if __name__ == "__main__":
    try:
        # هذه الطريقة هي المعيارية وتمنع حدوث أخطاء 
        # "Cannot close a running event loop"
        asyncio.run(main())
    except KeyboardInterrupt:
        # التعامل مع إيقاف البوت يدوياً بسلام
        pass
