-- Drop old tables if they exist
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS sales;

-- Products table
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barcode TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    category TEXT,
    quantity INTEGER DEFAULT 0,
    cost_price REAL DEFAULT 0,
    selling_price REAL DEFAULT 0,
    profit_margin REAL DEFAULT 0
);

-- Sales table (fixed with 'items' column)
CREATE TABLE sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    items TEXT NOT NULL,             -- JSON string of items
    total REAL NOT NULL,
    payment_method TEXT NOT NULL
);
