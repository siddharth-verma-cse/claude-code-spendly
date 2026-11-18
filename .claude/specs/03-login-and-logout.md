# Spec: Login and Logout

## Overview
Make sign-in and sign-out work. Right now `GET /login` shows a form whose `POST /login` has no handler, and `/logout` returns the placeholder string "Logout — coming in Step 3". This step adds a `POST /login` handler that looks up the user by email, checks the password with werkzeug, and stores the user in Flask's signed `session` cookie. It replaces the `/logout` placeholder with a route that clears the session. The navbar changes based on login state: logged-out visitors see "Sign in" / "Get started", logged-in users see their name and a "Sign out" button. Login is the first step that knows who the current user is, and every later step (profile in Step 4, expense CRUD in Steps 7–9) depends on `session["user_id"]`.

## Depends on
- **Step 1 — Database setup** (done): `users` table, `get_db()`, `PASSWORD_HASH_METHOD`, demo user `demo@spendly.com` from `seed_db()`.
- **Step 2 — Registration** (done): `get_user_by_email(conn, email)`, `app.secret_key`, and the flashed-message block on `login.html`.

## Routes
- `GET /login` — show the sign-in form (exists). If the user is already logged in, redirect to `/profile` instead — public
- `POST /login` — check email and password; on success clear the session, set `session["user_id"]` and `session["user_name"]`, flash "Welcome back, <name>." and redirect to `/profile`; on failure show `login.html` again with `error` and the email typed, status 401 (400 for empty fields) — public
- `POST /logout` — clear the session, flash "You have been signed out.", redirect to `/login` — logged-in (if not logged in, just redirect to `/login`)
- `GET /register` — (exists) add: if already logged in, redirect to `/profile` — public

Change the existing `login()` view to `@app.route("/login", methods=["GET", "POST"])` rather than adding a second function. Replace the placeholder `logout()` body and change it to `methods=["POST"]` — logout changes state, so it must not be a GET link (a third-party page could otherwise log the user out with an `<img src="/logout">`).

`/profile` stays the Step 4 placeholder; redirecting there now is intentional, so it becomes the real dashboard when Step 4 lands.

## Database changes
No database changes. The `users` table already has `email` and `password_hash`, and `get_user_by_email(conn, email)` already exists in `database/db.py`. No new helper is needed for this step.

## Templates
- **Create:** none
- **Modify:**
  - `templates/login.html` — fill the email input again with `value="{{ email or '' }}"` after a failed submit; never fill in the password; use `{{ url_for('login') }}` for the form action. Keep the existing flashed-message and `error` blocks.
  - `templates/base.html` — in `.nav-links` only: if `session.user_id` is set, show the user's name (`session.user_name`) and a small `<form method="POST" action="{{ url_for('logout') }}">` with a "Sign out" button; otherwise show the current "Sign in" / "Get started" links unchanged. Do not touch the footer or anything else.

## Files to change
- `app.py` — handle `POST /login`; implement `POST /logout`; redirect logged-in users away from `GET /login` and `GET /register`; import `session` from flask and `check_password_hash` from `werkzeug.security`; set `SESSION_COOKIE_SAMESITE = "Lax"`
- `templates/login.html` — keep typed email, `url_for` action
- `templates/base.html` — logged-in / logged-out navbar
- `static/css/style.css` — add `.nav-user` (name label) and `.nav-logout` (button styled like a nav link) next to the existing navbar styles

## Files to create
None.

## New dependencies
No new dependencies. Flask's `session` and `werkzeug.security.check_password_hash` are already installed.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only — reuse `get_user_by_email(conn, email)`; never format strings into SQL
- Passwords hashed with werkzeug — verify with `check_password_hash(row["password_hash"], password)`; never log, flash, or re-render the plain password
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- DB helpers take `conn` as a parameter; the route opens the connection with `get_db()` and closes it in `finally`
- Input handling for `POST /login`, in order:
  1. `email` — trim and lowercase (same as registration); `password` — do not trim
  2. If either is empty → "Please enter your email and password." (status 400)
  3. If no user has that email **or** the password does not match → the same message "Invalid email or password." (status 401). Never say which one was wrong.
- On successful login call `session.clear()` **before** setting `user_id` / `user_name`, so no data from an earlier session carries over
- Store only `user_id` (int) and `user_name` in the session — never the password hash or email
- Logout uses `session.clear()`, then flash, then redirect (POST/Redirect/GET)
- After a successful POST, always redirect — never render a page straight from a successful POST
- No `?next=` redirect parameter in this step (avoids open-redirect issues); always redirect to `/profile`
- Do not add a `login_required` decorator yet — no protected pages exist until Step 4
- Keep the change narrow: do not touch the landing, terms, privacy, register POST logic, or the other placeholder routes

## Definition of done
- [ ] `python app.py` starts without errors
- [ ] `GET /login` shows the form as before when logged out
- [ ] Signing in as `demo@spendly.com` / `demo123` redirects to `/profile` (still the Step 4 placeholder)
- [ ] After signing in, the navbar on any page (e.g. `/`, `/terms`) shows "Demo User" and a "Sign out" button instead of "Sign in" / "Get started"
- [ ] A wrong password shows "Invalid email or password.", keeps the email typed in, and the password field is empty
- [ ] An unknown email shows the exact same "Invalid email or password." message
- [ ] Email is matched case-insensitively and trimmed (`  DEMO@Spendly.com ` signs in)
- [ ] Submitting empty fields with `curl -d "email=&password="` returns 400 with "Please enter your email and password."
- [ ] A newly registered account (Step 2) can sign in with its password
- [ ] While logged in, visiting `/login` or `/register` redirects to `/profile`
- [ ] Clicking "Sign out" redirects to `/login`, shows "You have been signed out." once, and the navbar shows "Sign in" / "Get started" again
- [ ] `GET /logout` (typing it in the address bar) returns 405 and does not log the user out
- [ ] In browser DevTools, the `session` cookie is `HttpOnly` and `SameSite=Lax`, and its decoded contents hold only `user_id` and `user_name`
- [ ] No hex values added to `style.css` — new navbar styles use CSS variables only
