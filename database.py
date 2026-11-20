import aiosqlite
from datetime import datetime
from config import DB_PATH

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Foydalanuvchilar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                balance INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # O'yinlar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                category TEXT NOT NULL, -- 'paid' yoki 'free'
                price INTEGER DEFAULT 0,
                photo_file_id TEXT,
                game_file_id TEXT NOT NULL,
                downloads_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Xaridlar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                game_id INTEGER NOT NULL,
                amount INTEGER DEFAULT 0,
                purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (game_id) REFERENCES games(id)
            )
        """)
        
        # To'lovlar jadvali (TolovAPI)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_id TEXT UNIQUE NOT NULL,
                order_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                card_number TEXT,
                status TEXT DEFAULT 'pending', -- pending, paid, cancel
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Majburiy kanallar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                url TEXT NOT NULL
            )
        """)

        # Maxfiy kanallarga a'zo bo'lish so'rovlari (Join requests) jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS join_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                channel_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, channel_id)
            )
        """)
        
        await db.commit()

# --- Foydalanuvchilar ---
async def add_or_update_user(user_id: int, username: str, full_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id, balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                await db.execute(
                    "UPDATE users SET username = ?, full_name = ?, last_active = CURRENT_TIMESTAMP WHERE user_id = ?",
                    (username, full_name, user_id)
                )
            else:
                await db.execute(
                    "INSERT INTO users (user_id, username, full_name, balance) VALUES (?, ?, ?, 0)",
                    (user_id, username, full_name)
                )
        await db.commit()

async def get_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone()

async def update_user_balance(user_id: int, amount_change: int):
    """Balansni oshirish yoki kamaytirish (musbat yoki manfiy)."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount_change, user_id))
        await db.commit()

async def set_user_balance(user_id: int, new_balance: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id))
        await db.commit()

async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users") as cursor:
            return await cursor.fetchall()

# --- O'yinlar ---
async def add_game(title: str, description: str, category: str, price: int, photo_file_id: str, game_file_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO games (title, description, category, price, photo_file_id, game_file_id) VALUES (?, ?, ?, ?, ?, ?)",
            (title, description, category, price, photo_file_id, game_file_id)
        )
        await db.commit()
        return cursor.lastrowid

async def get_game(game_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM games WHERE id = ?", (game_id,)) as cursor:
            return await cursor.fetchone()

async def delete_game(game_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM games WHERE id = ?", (game_id,))
        await db.commit()

async def get_games_paginated(category: str, page: int = 1, per_page: int = 6):
    offset = (page - 1) * per_page
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM games WHERE category = ? ORDER BY id DESC LIMIT ? OFFSET ?",
            (category, per_page, offset)
        ) as cursor:
            return await cursor.fetchall()

async def count_games(category: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM games WHERE category = ?", (category,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

async def increment_game_downloads(game_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE games SET downloads_count = downloads_count + 1 WHERE id = ?", (game_id,))
        await db.commit()

# --- Xaridlar ---
async def add_purchase(user_id: int, game_id: int, amount: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO purchases (user_id, game_id, amount) VALUES (?, ?, ?)",
            (user_id, game_id, amount)
        )
        await db.commit()

async def has_user_purchased(user_id: int, game_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id FROM purchases WHERE user_id = ? AND game_id = ?",
            (user_id, game_id)
        ) as cursor:
            row = await cursor.fetchone()
            return row is not None

async def get_user_purchases_list(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT p.id as purchase_id, p.purchased_at, p.amount, g.*
            FROM purchases p
            JOIN games g ON p.game_id = g.id
            WHERE p.user_id = ?
            ORDER BY p.id DESC
        """, (user_id,)) as cursor:
            return await cursor.fetchall()

async def count_user_purchases(user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM purchases WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

# --- To'lovlar ---
async def save_payment_record(payment_id: str, order_id: str, user_id: int, amount: int, card_number: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO payments (payment_id, order_id, user_id, amount, card_number, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
        """, (payment_id, order_id, user_id, amount, card_number))
        await db.commit()

async def get_payment_record(payment_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM payments WHERE payment_id = ?", (payment_id,)) as cursor:
            return await cursor.fetchone()

async def mark_payment_paid(payment_id: str) -> bool:
    """Agar payment_id holati pending bo'lsa paid qilib True qaytaradi, aks holda False (faqat 1 marta hisoblash)."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT status FROM payments WHERE payment_id = ?", (payment_id,)) as cursor:
            row = await cursor.fetchone()
            if not row or row[0] != 'pending':
                return False
        await db.execute(
            "UPDATE payments SET status = 'paid', updated_at = CURRENT_TIMESTAMP WHERE payment_id = ?",
            (payment_id,)
        )
        await db.commit()
        return True

async def mark_payment_cancelled(payment_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE payments SET status = 'cancel', updated_at = CURRENT_TIMESTAMP WHERE payment_id = ?",
            (payment_id,)
        )
        await db.commit()

async def get_pending_payments():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM payments WHERE status = 'pending' ORDER BY id DESC") as cursor:
            return await cursor.fetchall()

# --- Kanallar ---
async def get_channels():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM channels") as cursor:
            return await cursor.fetchall()

async def add_channel(channel_id: str, title: str, url: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO channels (channel_id, title, url) VALUES (?, ?, ?)",
            (channel_id, title, url)
        )
        await db.commit()

async def delete_channel(channel_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,))
        await db.commit()

# --- So'rovlar (Join Requests) ---
async def add_join_request(user_id: int, channel_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO join_requests (user_id, channel_id) VALUES (?, ?)",
            (user_id, str(channel_id))
        )
        await db.commit()

async def has_sent_join_request(user_id: int, channel_id: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        # channel_id -100 li yoki oddiy string bo'lishi mumkin
        ch_str = str(channel_id)
        async with db.execute(
            "SELECT id FROM join_requests WHERE user_id = ? AND (channel_id = ? OR channel_id = ?)",
            (user_id, ch_str, ch_str.replace("-100", "-"))
        ) as cursor:
            row = await cursor.fetchone()
            return row is not None

# --- Statistika ---
async def get_system_statistics():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as c:
            total_users = (await c.fetchone())[0]
            
        async with db.execute("SELECT COUNT(*) FROM users WHERE DATE(created_at) = DATE('now', 'localtime')") as c:
            today_users = (await c.fetchone())[0]
            
        async with db.execute("SELECT COUNT(DISTINCT user_id) FROM payments WHERE status = 'paid'") as c:
            paid_users_count = (await c.fetchone())[0]
            
        async with db.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM payments 
            WHERE status = 'paid' AND strftime('%Y-%m', updated_at) = strftime('%Y-%m', 'now', 'localtime')
        """) as c:
            monthly_income = (await c.fetchone())[0]
            
        async with db.execute("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = 'paid'") as c:
            total_income = (await c.fetchone())[0]
            
        async with db.execute("SELECT COUNT(*) FROM games") as c:
            total_games = (await c.fetchone())[0]
            
        async with db.execute("SELECT COUNT(*) FROM games WHERE category = 'paid'") as c:
            paid_games = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM games WHERE category = 'free'") as c:
            free_games = (await c.fetchone())[0]

        async with db.execute("SELECT COUNT(*) FROM purchases") as c:
            total_purchases = (await c.fetchone())[0]
            
        return {
            "total_users": total_users,
            "today_users": today_users,
            "paid_users_count": paid_users_count,
            "free_users_count": total_users - paid_users_count if total_users >= paid_users_count else 0,
            "monthly_income": monthly_income,
            "total_income": total_income,
            "total_games": total_games,
            "paid_games": paid_games,
            "free_games": free_games,
            "total_purchases": total_purchases
        }
