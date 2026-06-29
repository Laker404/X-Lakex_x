import aiosqlite

DB_PATH = "bot.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS location (
                id INTEGER PRIMARY KEY, name TEXT, x REAL, y REAL, z REAL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS client (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_id INTEGER UNIQUE,
                discord_tag TEXT,
                status TEXT DEFAULT 'new',
                discount REAL DEFAULT 0.0,
                order_count INTEGER DEFAULT 0,
                ticket INTEGER
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT, action TEXT, time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS price (
                id INTEGER PRIMARY KEY, service TEXT, description TEXT,
                rub REAL, eur REAL, dollar REAL, virtual REAL, crypto REAL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS promocode (
                id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, description TEXT,
                limit_count INTEGER, uses_count INTEGER DEFAULT 0, used_by TEXT
            )
        """)
        await db.commit()

async def sync_member(discord_id: int, discord_tag: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO client (discord_id, discord_tag)
            VALUES (?, ?)
            ON CONFLICT(discord_id) DO UPDATE SET discord_tag = excluded.discord_tag
        """, (discord_id, discord_tag))
        await db.commit()

async def log_action(log_type: str, action: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO logs (type, action) VALUES (?, ?)", (log_type, action))
        await db.commit()