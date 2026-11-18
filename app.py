import os
import re
import secrets
import sqlite3

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
    return "Profile page — coming in Step 4"


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
