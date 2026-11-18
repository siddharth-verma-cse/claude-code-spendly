import os
import re
import secrets
import sqlite3
from datetime import datetime

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from database.db import create_user, get_db, get_user_by_email, init_db, seed_db

app = Flask(__name__)
# Set SPENDLY_SECRET_KEY in the environment for stable sessions; the random
# fallback is fine for dev but invalidates sessions on every restart.
app.secret_key = os.environ.get("SPENDLY_SECRET_KEY") or secrets.token_hex(32)
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

with app.app_context():
    init_db()
    seed_db(dev_mode=(__name__ == "__main__" or app.debug))


@app.after_request
def no_store_auth_pages(response):
    # Stop the browser from showing a cached /login or /register page via the
    # Back button after the user signs in; force a fresh request so the
    # "already logged in" redirect runs.
    if request.endpoint in ("login", "register"):
        response.headers["Cache-Control"] = "no-store"
    return response


# ------------------------------------------------------------------ #
# Template filters                                                    #
# ------------------------------------------------------------------ #

@app.template_filter("inr")
def format_inr(amount):
    """Format a number as rupees with Indian digit grouping: 124500 -> ₹1,24,500."""
    n = int(round(amount))
    sign = "-" if n < 0 else ""
    digits = str(abs(n))
    if len(digits) > 3:
        head, tail = digits[:-3], digits[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        digits = ",".join(groups) + "," + tail
    return f"{sign}₹{digits}"


@app.template_filter("short_date")
def format_short_date(iso_date):
    """Turn a stored ISO date ('2026-11-15') into '15 Nov'."""
    d = datetime.strptime(iso_date, "%Y-%m-%d")
    return f"{d.day} {d.strftime('%b')}"


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        if session.get("user_id"):
            return redirect(url_for("profile"))
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    error = None
    if not name or len(name) > 100:
        error = "Please enter your name."
    elif not EMAIL_RE.match(email):
        error = "Please enter a valid email address."
    elif len(password) < 8:
        error = "Password must be at least 8 characters."

    if error is None:
        conn = get_db()
        try:
            if get_user_by_email(conn, email):
                error = "An account with this email already exists."
            else:
                create_user(conn, name, email, password)
                conn.commit()
        except sqlite3.IntegrityError:
            error = "An account with this email already exists."
        finally:
            conn.close()

    if error:
        return render_template("register.html", error=error, name=name, email=email), 400

    flash("Account created — please sign in.", "success")
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if session.get("user_id"):
            return redirect(url_for("profile"))
        return render_template("login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not email or not password:
        return render_template(
            "login.html", error="Please enter your email and password.", email=email
        ), 400

    conn = get_db()
    try:
        user = get_user_by_email(conn, email)
    finally:
        conn.close()

    # Same message for unknown email and wrong password, so the page
    # doesn't reveal which emails have accounts.
    if user is None or not check_password_hash(user["password_hash"], password):
        return render_template(
            "login.html", error="Invalid email or password.", email=email
        ), 401

    # Clear first so nothing from an earlier session carries over.
    session.clear()
    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    flash(f"Welcome back, {user['name']}.", "success")
    return redirect(url_for("profile"))


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout", methods=["POST"])
def logout():
    was_logged_in = "user_id" in session
    session.clear()
    if was_logged_in:
        flash("You have been signed out.", "success")
    return redirect(url_for("login"))


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    # Step 4 is UI-only: hardcoded data shaped like the rows Step 5's
    # queries will return, so that step only swaps the data source.
    user = {
        "name": "Demo User",
        "email": "demo@spendly.com",
        "member_since": "January 2026",
        "initials": "DU",
    }

    # Newest first, matching the demo user's seed expenses.
    transactions = [
        {"date": "2026-11-15", "description": "Dinner out", "category": "Food", "amount": 780.00},
        {"date": "2026-11-13", "description": "Gift wrap", "category": "Other", "amount": 300.00},
        {"date": "2026-11-11", "description": "Shoes", "category": "Shopping", "amount": 2299.00},
        {"date": "2026-11-09", "description": "Movie tickets", "category": "Entertainment", "amount": 499.00},
        {"date": "2026-11-07", "description": "Pharmacy", "category": "Health", "amount": 600.00},
        {"date": "2026-11-05", "description": "Electricity bill", "category": "Bills", "amount": 1850.00},
        {"date": "2026-11-03", "description": "Metro card top-up", "category": "Transport", "amount": 120.00},
        {"date": "2026-11-01", "description": "Groceries", "category": "Food", "amount": 450.00},
    ]

    # Derive totals from the rows so the stats and breakdown always agree.
    total_spent = sum(tx["amount"] for tx in transactions)
    by_category = {}
    for tx in transactions:
        by_category[tx["category"]] = by_category.get(tx["category"], 0) + tx["amount"]

    categories = [
        {"name": name, "total": total, "pct": round(total / total_spent * 100)}
        for name, total in sorted(by_category.items(), key=lambda item: item[1], reverse=True)
    ]

    stats = {
        "total_spent": total_spent,
        "tx_count": len(transactions),
        "top_category": categories[0]["name"],
    }

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        transactions=transactions,
        categories=categories,
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
