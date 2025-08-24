from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_cors import CORS
import sqlite3, os, json
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecret"  # for login session
CORS(app)




# Always use the real DB file (update path to your actual DB location)
DB = os.path.join("C:/Users/K/Desktop/Soe_het_Pos/data", "pos_system.db")

# --- Database Init ---
def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

        # ✅ products table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        barcode TEXT,
        name TEXT NOT NULL,
        category TEXT,
        quantity INTEGER DEFAULT 0,
        cost_price REAL DEFAULT 0,
        selling_price REAL DEFAULT 0,
        profit_margin REAL DEFAULT 0
    )
    """)

    # ✅ outflow table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS outflow (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        amount REAL NOT NULL,
        date TEXT DEFAULT (DATE('now','localtime'))
    )
    """)

    # ✅ sales table (now with payment_method)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        items TEXT NOT NULL,
        total REAL NOT NULL,
        cash_received REAL DEFAULT 0,
        change_amount REAL DEFAULT 0,
        payment_method TEXT DEFAULT 'Cash',
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


# --- Pages ---
@app.route("/")
def home():
    # default homepage → redirect to products
    return redirect(url_for("products_page"))

@app.route("/products")
def products_page():
    return render_template("index.html")

@app.route("/cashier")
def cashier():
    return render_template("temp_pos.html")


@app.route("/api/outflow", methods=["POST"])
def add_outflow():
    data = request.json
    name = data.get("name")
    amount = data.get("amount")

    if not name or not amount:
        return jsonify({"success": False, "error": "Missing fields"}), 400

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("INSERT INTO outflow (name, amount, date) VALUES (?, ?, DATE('now','localtime'))",
                (name, amount))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Outflow recorded"})








@app.route("/api/outflow")
def get_outflows():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    rows = cur.execute("SELECT * FROM outflow ORDER BY date DESC").fetchall()
    conn.close()
    return jsonify(success=True, data=[dict(r) for r in rows])

# ---------- Update Outflow ----------
@app.route('/api/outflow/<int:id>', methods=['PUT'])
def update_outflow(id):
    data = request.json
    name = data.get('name')
    amount = data.get('amount')

    if not name or amount is None:
        return jsonify({"success": False, "error": "Missing fields"}), 400

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("UPDATE outflow SET name=?, amount=? WHERE id=?", (name, amount, id))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Outflow updated"})


# ---------- Delete Outflow ----------
@app.route('/api/outflow/<int:id>', methods=['DELETE'])
def delete_outflow(id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("DELETE FROM outflow WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Outflow deleted"})





@app.route("/api/restock", methods=["POST"])
def restock_product():
    try:
        data = request.json
        if not data:
            return jsonify(success=False, error="No JSON received"), 400

        product_id = int(data["product_id"])
        qty = int(data["qty"])
        cost_price = float(data["cost_price"])
        shop_name = data["shop_name"]
        date = data["date"]

        # ✅ Use the same DB as everywhere else
        conn = sqlite3.connect("pos_system.db")
        c = conn.cursor()

        # Create restock history table if not exists
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

        # Insert into restocks history
        c.execute("""
            INSERT INTO restocks (product_id, qty, cost_price, shop_name, date)
            VALUES (?, ?, ?, ?, ?)
        """, (product_id, qty, cost_price, shop_name, date))

        # Update product stock & average cost price
        c.execute("SELECT quantity, cost_price FROM products WHERE id=?", (product_id,))
        row = c.fetchone()
        if row:
            old_qty, old_cost = row
            new_qty = old_qty + qty
            new_cost = ((old_qty * old_cost) + (qty * cost_price)) / new_qty
            c.execute("UPDATE products SET quantity=?, cost_price=? WHERE id=?",
                      (new_qty, new_cost, product_id))

        conn.commit()
        conn.close()

        return jsonify(success=True, message="Restock saved")

    except Exception as e:
        return jsonify(success=False, error=str(e)), 500
@app.route("/api/search_products")
def search_products():
    query = request.args.get("q", "")
    conn = sqlite3.connect("pos_system.db")
    c = conn.cursor()
    c.execute("""
        SELECT id, name, barcode, quantity 
        FROM products 
        WHERE name LIKE ? OR barcode LIKE ?
        LIMIT 10
    """, (f"%{query}%", f"%{query}%"))
    products = [
        {"id": row[0], "name": row[1], "barcode": row[2], "stock": row[3]}
        for row in c.fetchall()
    ]
    conn.close()
    return jsonify(products)


@app.route("/api/restock_records")
def restock_records():
    shop = request.args.get("shop")
    month = request.args.get("month")
    year = request.args.get("year")
    date = request.args.get("date")

    query = "SELECT r.id, p.name, r.qty, r.cost_price, r.shop_name, r.date FROM restocks r JOIN products p ON r.product_id=p.id WHERE 1=1"
    params = []

    if shop:
        query += " AND r.shop_name=?"
        params.append(shop)
    if month and year:
        query += " AND strftime('%m', r.date)=? AND strftime('%Y', r.date)=?"
        params.extend([f"{int(month):02d}", str(year)])
    if date:
        query += " AND r.date=?"
        params.append(date)

    query += " ORDER BY r.date DESC"

    conn = sqlite3.connect("pos_system.db")
    c = conn.cursor()
    c.execute(query, params)
    records = [
        {"id": row[0], "product": row[1], "qty": row[2], "cost_price": row[3], "shop": row[4], "date": row[5]}
        for row in c.fetchall()
    ]
    conn.close()
    return jsonify(records)


@app.route("/sales")
def sales_page():
    return render_template("sales.html")

@app.route("/sales/history")
def sales_history_page():
    return render_template("sales_history.html")


@app.route('/profit')
def profit():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    import json
  try:
      # ---------- Daily & Monthly Profit Calculation ----------
    today = datetime.now().strftime("%Y-%m-%d")
    this_month = datetime.now().strftime("%Y-%m")

    cur.execute("SELECT items, timestamp FROM sales")
    sales_rows = cur.fetchall()

    today_profit = 0
    month_profit = 0
    total_transactions = 0

    daily_sales_dict = {}

    for items_json, ts in sales_rows:
        try:
            items = json.loads(items_json)
        except:
            items = []

        is_today = ts.startswith(today)
        is_month = ts.startswith(this_month)

        if is_today:
            total_transactions += 1

        for item in items:
            profit_val = (item.get("price", 0) - item.get("cost_price", 0)) * item.get("qty", 0)

            if is_today:
                today_profit += profit_val

                # group by barcode
                barcode = item.get("barcode", "")
                if barcode not in daily_sales_dict:
                    daily_sales_dict[barcode] = {
                        "barcode": barcode,
                        "name": item.get("name", ""),
                        "qty": 0,
                        "profit": 0,
                        "timestamp": ts
                    }
                daily_sales_dict[barcode]["qty"] += item.get("qty", 0)
                daily_sales_dict[barcode]["profit"] += profit_val

            if is_month:
                month_profit += profit_val


# ✅ round all daily profits before sending to template
        for v in daily_sales_dict.values():
               v["profit"] = round(v["profit"], 2)

    # ---------- Outflows ----------
    cur.execute("SELECT SUM(amount) FROM outflow WHERE DATE(date)=DATE('now','localtime')")
    today_outflow = cur.fetchone()[0] or 0

    cur.execute("SELECT SUM(amount) FROM outflow WHERE strftime('%Y-%m', date)=strftime('%Y-%m','now','localtime')")
    month_outflow = cur.fetchone()[0] or 0

    conn.close()

    # Final profit after outflow
    today_profit_including_outflow = today_profit - today_outflow
    month_profit_including_outflow = month_profit - month_outflow

    return render_template(
    'profit.html',
    today_profit=round(today_profit, 2),
    today_profit_including_outflow=round(today_profit_including_outflow, 2),
    month_profit=round(month_profit, 2),
    month_profit_including_outflow=round(month_profit_including_outflow, 2),
    total_transactions=total_transactions,
    daily_sales=list(daily_sales_dict.values())
)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"<h1>ERROR in /profit</h1><pre>{e}</pre>", 500



@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == "admin" and password == "1234":
            session["logged_in"] = True
            return redirect(url_for("profit_page"))
        else:
            return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# --- Products API ---
@app.route("/api/products", methods=["GET"])
def get_products():
    try:
        conn = sqlite3.connect(DB)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM products")
        rows = cur.fetchall()
        conn.close()
        return jsonify({"success": True, "data": [dict(r) for r in rows]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/products", methods=["POST"])
def add_product():
    data = request.json
    try:
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute("""INSERT INTO products (barcode, name, category, quantity, cost_price, selling_price, profit_margin)
                       VALUES (?,?,?,?,?,?,?)""",
                    (data.get("barcode"), data["name"], data.get("category"),
                     data.get("quantity", 0), data.get("cost_price", 0),
                     data.get("selling_price", 0), data.get("profit_margin", 0)))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/products/<int:pid>", methods=["PUT"])
def update_product(pid):
    data = request.json
    try:
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute("""UPDATE products
                       SET barcode=?, name=?, category=?, quantity=?, cost_price=?, selling_price=?
                       WHERE id=?""",
                    (data.get("barcode"), data["name"], data.get("category"),
                     data.get("quantity", 0), data.get("cost_price", 0),
                     data.get("selling_price", 0), pid))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/products/<int:pid>", methods=["DELETE"])
def delete_product(pid):
    try:
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute("DELETE FROM products WHERE id=?", (pid,))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# --- Sales API ---
@app.route("/api/sales", methods=["GET"])
def get_sales():
    try:
        from_date = request.args.get("from")
        to_date = request.args.get("to")

        conn = sqlite3.connect(DB)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        if from_date and to_date:
            cur.execute("SELECT * FROM sales WHERE date(timestamp) BETWEEN ? AND ? ORDER BY timestamp DESC", (from_date, to_date))
        else:
            cur.execute("SELECT * FROM sales ORDER BY timestamp DESC")

        rows = cur.fetchall()
        conn.close()
        return jsonify({"success": True, "data": [dict(r) for r in rows]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})



@app.route("/api/sales", methods=["POST"])
def add_sale():
    data = request.json
    try:
        items = data.get("items", [])

        # 🚨 prevent empty/invalid sales being saved
        if not items or len(items) == 0:
            return jsonify({"success": False, "error": "No items in sale"}), 400

        conn = sqlite3.connect(DB)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        enriched_items = []
        for item in items:
            barcode = item.get("barcode")
            qty = int(item.get("qty", 1))

            # fetch cost price
            cur.execute("SELECT cost_price FROM products WHERE barcode = ?", (barcode,))
            row = cur.fetchone()
            cost_price = row["cost_price"] if row else 0

            enriched_items.append({
                "barcode": barcode,
                "name": item.get("name", ""),
                "qty": qty,
                "price": float(item.get("price", 0)),
                "cost_price": float(cost_price)
            })

            # decrease stock safely
            if barcode:
                cur.execute("""
                    UPDATE products 
                    SET quantity = CASE WHEN quantity - ? < 0 THEN 0 ELSE quantity - ? END 
                    WHERE barcode = ?
                """, (qty, qty, barcode))

        # insert only if there are items
        if enriched_items:
            items_json = json.dumps(enriched_items)
            total = float(data.get("total", 0))
            cash_received = float(data.get("cash_received", 0))
            change_amount = float(data.get("change_amount", 0))
            payment_method = data.get("payment_method", "Cash")

        # ✅ insert including payment_method
        cur.execute("""
            INSERT INTO sales (items, total, cash_received, change_amount, payment_method, timestamp) 
            VALUES (?, ?, ?, ?, ?, datetime('now','localtime'))
        """, (items_json, total, cash_received, change_amount, payment_method))

        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": f"✅ Sale recorded ({payment_method})"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# --- Reports API ---
@app.route("/api/sales/report", methods=["GET"])
def sales_report():
    try:
        conn = sqlite3.connect(DB)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM sales")
        sales = cur.fetchall()
        conn.close()

        today = datetime.today().strftime("%Y-%m-%d")
        month = datetime.today().strftime("%Y-%m")

        daily_total, monthly_total, daily_profit, monthly_profit = 0, 0, 0, 0
        daily_transactions, monthly_transactions = 0, 0

        for s in sales:
            ts = s["timestamp"] or ""
            try:
                sale_items = json.loads(s["items"]) if s["items"] else []
            except:
                sale_items = []
            sale_total = s["total"]

            # --- daily ---
            if ts.startswith(today):
                daily_total += sale_total
                daily_transactions += 1
                for item in sale_items:
                    profit = (item.get("price", 0) - item.get("cost_price", 0)) * item.get("qty", 0)
                    daily_profit += profit

            # --- monthly ---
            if ts.startswith(month):
                monthly_total += sale_total
                monthly_transactions += 1
                for item in sale_items:
                    profit = (item.get("price", 0) - item.get("cost_price", 0)) * item.get("qty", 0)
                    monthly_profit += profit

        return jsonify({
            "success": True,
            "daily": {"revenue": daily_total, "transactions": daily_transactions, "profit": daily_profit},
            "monthly": {"revenue": monthly_total, "transactions": monthly_transactions, "profit": monthly_profit}
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

    # --- Reset Sales API ---
@app.route("/api/sales/reset", methods=["POST"])
def reset_sales():
    try:
        scope = request.json.get("scope", "all")  # "daily" or "all"
        conn = sqlite3.connect(DB)
        cur = conn.cursor()

        if scope == "daily":
            today = datetime.today().strftime("%Y-%m-%d")
            cur.execute("DELETE FROM sales WHERE DATE(timestamp) = ?", (today,))
        else:
            cur.execute("DELETE FROM sales")

        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": f"✅ {scope.capitalize()} sales reset successfully"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})



@app.route('/api/low_stock')
def api_low_stock():
    conn = sqlite3.connect('pos_system.db')
    c = conn.cursor()
    c.execute("SELECT id, barcode, name, category, quantity, cost_price, selling_price FROM products WHERE quantity < 10")
    products = c.fetchall()
    conn.close()

    # Convert to JSON
    data = []
    for p in products:
        data.append({
            "id": p[0],
            "barcode": p[1],
            "name": p[2],
            "category": p[3],
            "qty": p[4],
            "cost": p[5],
            "selling": p[6],
            "status": "Out of Stock" if p[4] == 0 else "Low Stock"
        })
    return jsonify(data)



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


