def init_db():
    conn = sqlite3.connect("pos_system.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS restocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        qty INTEGER,
        cost_price REAL,
        shop_name TEXT,
        date TEXT
    )
    """)

    # Speeds up search
    c.execute("CREATE INDEX IF NOT EXISTS idx_restocks_date ON restocks(date)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_restocks_shop ON restocks(shop_name)")
    conn.commit()
    conn.close()
