import os
import re
import secrets
import sqlite3

from flask import Flask, flash, redirect, render_template, request, url_for

from database.db import create_user, get_db, get_user_by_email, init_db, seed_db

app = Flask(__name__)
# Set SPENDLY_SECRET_KEY in the environment for stable sessions; the random
# fallback is fine for dev but invalidates sessions on every restart.
app.secret_key = os.environ.get("SPENDLY_SECRET_KEY") or secrets.token_hex(32)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

with app.app_context():
    init_db()
    seed_db(dev_mode=(__name__ == "__main__" or app.debug))


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
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


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    return "Logout — coming in Step 3"


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
