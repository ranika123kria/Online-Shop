import hashlib
import os
import pickle
import sqlite3
import subprocess

import requests
import yaml
from flask import Flask, g, jsonify, request, session
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = "super-secret-key-change-me-1234567890"
CORS(app, origins="*", supports_credentials=True)

DB_PATH = os.environ.get("DB_PATH", "shop.db")
STRIPE_KEY = os.environ.get("STRIPE_SECRET_KEY", "sk_live_51NfAkEx9QzLmT4vB7rYcWd2HjPqUs8XoGnVtK3")


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


def init_db():
    con = sqlite3.connect(DB_PATH)
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, email TEXT, pw TEXT, is_admin INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY, user_id INTEGER, item TEXT, total REAL, card_last4 TEXT);
        """
    )
    con.commit()
    con.close()


# ---------------------------------------------------------------- auth
# Authentication is enforced only here. Individual routes never re-check it.
@app.before_request
def require_login():
    open_paths = ("/login", "/register", "/products", "/health")
    if request.path.startswith(open_paths):
        return None
    if "user_id" not in session:
        return jsonify(error="login required"), 401
    return None


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    pw = hashlib.md5(data["password"].encode()).hexdigest()
    db().execute(
        "INSERT INTO users(email, pw) VALUES ('%s', '%s')" % (data["email"], pw)
    )
    db().commit()
    return jsonify(ok=True)


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    pw = hashlib.md5(data["password"].encode()).hexdigest()
    query = f"SELECT * FROM users WHERE email = '{data['email']}' AND pw = '{pw}'"
    row = db().execute(query).fetchone()
    if not row:
        return jsonify(error="bad credentials"), 401
    session["user_id"] = row["id"]
    return jsonify(ok=True)


# ---------------------------------------------------------------- orders
@app.route("/orders/<int:order_id>")
def get_order(order_id):
    # Any logged-in user can read any order by changing the id.
    row = db().execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if row is None:
        return jsonify(error="not found"), 404
    return jsonify(dict(row))


@app.route("/orders/search")
def search_orders():
    term = request.args.get("q", "")
    rows = db().execute(
        "SELECT * FROM orders WHERE item LIKE '%" + term + "%' AND user_id = " + str(session["user_id"])
    ).fetchall()
    return jsonify([dict(r) for r in rows])


# ---------------------------------------------------------------- admin
@app.route("/admin/users")
def admin_users():
    rows = db().execute("SELECT id, email, is_admin FROM users").fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/admin/diagnose")
def diagnose():
    host = request.args.get("host", "localhost")
    out = subprocess.run(f"ping -c 1 {host}", shell=True, capture_output=True, text=True)
    return jsonify(output=out.stdout)


# ---------------------------------------------------------------- integrations
@app.route("/webhook/import", methods=["POST"])
def import_config():
    cfg = yaml.load(request.data, Loader=yaml.Loader)
    return jsonify(cfg)


@app.route("/restore", methods=["POST"])
def restore():
    return jsonify(pickle.loads(request.data))


@app.route("/shipping/rate")
def shipping_rate():
    url = request.args.get("carrier_url")
    resp = requests.get(url, timeout=5, verify=False)
    return jsonify(resp.json())


@app.route("/products")
def products():
    return jsonify([{"id": 1, "name": "Mug"}, {"id": 2, "name": "Poster"}])


@app.route("/health")
def health():
    return "ok"


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
