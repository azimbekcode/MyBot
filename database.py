import asyncpg
import os
import logging
from datetime import datetime

class Database:
    def __init__(self, db_url):
        self.db_url = db_url
        self.pool = None

    async def connect(self):
        try:
            self.pool = await asyncpg.create_pool(self.db_url)
            # Create tables if not exists
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id BIGINT PRIMARY KEY,
                        username TEXT,
                        full_name TEXT,
                        joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    CREATE TABLE IF NOT EXISTS settings (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    );
                    
                    -- Default settings if not exist
                    INSERT INTO settings (key, value) VALUES ('bot_news', '@AzimbekDeveloper') ON CONFLICT DO NOTHING;
                    INSERT INTO settings (key, value) VALUES ('welcome_text', 'Botga xush kelibsiz!') ON CONFLICT DO NOTHING;
                """)
            logging.info("PostgreSQL-ga ulanish muvaffaqiyatli!")
        except Exception as e:
            logging.error(f"DB ulanish xatosi: {e}")

    async def add_user(self, user_id, username, full_name):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO users (user_id, username, full_name) 
                VALUES ($1, $2, $3) 
                ON CONFLICT (user_id) DO UPDATE SET username = $2, full_name = $3
            """, user_id, username, full_name)

    async def get_all_users(self):
        async with self.pool.acquire() as conn:
            return await conn.fetch("SELECT * FROM users ORDER BY joined_date DESC")

    async def delete_user(self, user_id):
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM users WHERE user_id = $1", user_id)

    async def get_user_count(self):
        async with self.pool.acquire() as conn:
            return await conn.fetchval("SELECT COUNT(*) FROM users")

    async def get_settings(self):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT key, value FROM settings")
            return {row['key']: row['value'] for row in rows}

    async def update_setting(self, key, value):
        async with self.pool.acquire() as conn:
            await conn.execute("INSERT INTO settings (key, value) VALUES ($1, $2) ON CONFLICT (key) DO UPDATE SET value = $2", key, value)

    async def close(self):
        if self.pool:
            await self.pool.close()
