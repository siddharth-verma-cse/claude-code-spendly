# Spec: Registration

## Overview
Make the existing `/register` page work. Right now `GET /register` shows a form whose `POST /register` has no handler. This step adds that handler: it checks the name, email and password, hashes the password with werkzeug and creates a row in `users`. On success it sends the user to `/login` with a "Account created — please sign in" message. On failure it shows the form again with an error and keeps the values the user typed (except the password). Registration is the first step that writes data from a user, and Step 3 (login/logout) needs real accounts to sign in with.

## Depends on
- **Step 1 — Database setup** (done): `users` table with `UNIQUE` email, `get_db()`, and `PASSWORD_HASH_METHOD` in `database/db.py`.

## Routes
- `GET /register` — show the registration form (exists; keep as is, but allow form values and errors to be passed in) — public
- `POST /register` — check input, create the user, redirect to `/login` with a success flash message; on failure show `register.html` again with `error` and the values typed — public

Change the existing `register()` view to `@app.route("/register", methods=["GET", "POST"])` rather than adding a second function.

## Database changes
No database changes. The current `users` table (`id`, `name`, `email UNIQUE NOT NULL`, `password_hash`, `created_at`) already covers registration.

Add two small helpers to `database/db.py` so the SQL stays out of `app.py`:
- `get_user_by_email(email)` — returns the `sqlite3.Row` or `None`
- `create_user(name, email, password)` — hashes the password with `generate_password_hash(password, method=PASSWORD_HASH_METHOD)`, inserts the row, commits, returns the new `id`

## Templates
- **Create:** none
- **Modify:**
  - `templates/register.html` — fill the `name` and `email` inputs again with `value="{{ name or '' }}"` / `value="{{ email or '' }}"` after a failed submit; never fill in the password; add `minlength="8"` to the password input. Use `{{ url_for('register') }}` for the form action.
  - `templates/login.html` — show flashed messages (category `success`) above the form using `get_flashed_messages(with_categories=true)`, styled with a new `.auth-success` class. Change nothing else on the page.

## Files to change
- `app.py` — handle `POST /register`; import `request`, `redirect`, `url_for`, `flash`; set `app.secret_key` (needed for `flash`)
- `database/db.py` — add `get_user_by_email()` and `create_user()`
- `templates/register.html` — keep typed values, `minlength`, `url_for` action
- `templates/login.html` — show flashed success message
- `static/css/style.css` — add `.auth-success` next to the existing `.auth-error`

## Files to create
None.

## New dependencies
No new dependencies. Flask's `flash` and `werkzeug.security` are already installed.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only — never format strings into SQL
- Passwords hashed with werkzeug: `generate_password_hash(password, method=PASSWORD_HASH_METHOD)`; never store or log the plain password
- Use CSS variables — never hardcode hex values (`.auth-success` uses `--accent` / `--accent-light`)
- All templates extend `base.html`
- `app.secret_key` comes from the environment variable `SPENDLY_SECRET_KEY`; if it is not set, fall back to `secrets.token_hex(32)` (fine for dev, but sessions reset when the server restarts). Never write a secret key into the code.
- Input checks run on the server, in this order, and stop at the first error:
  1. `name` — remove spaces from both ends; must not be empty; at most 100 characters
  2. `email` — remove spaces from both ends and make lowercase; must match a basic `something@something.something` pattern
  3. `password` — at least 8 characters (do not trim it)
  4. email not already registered (`get_user_by_email`)
- Also catch `sqlite3.IntegrityError` from the insert (two sign-ups racing for the same email) and show the same "already exists" error
- Error messages: "Please enter your name.", "Please enter a valid email address.", "Password must be at least 8 characters.", "An account with this email already exists."
- After a successful POST, redirect (POST/Redirect/GET) — never render a page straight from a successful POST
- Do not log the user in automatically — sessions and login arrive in Step 3
- Keep the change narrow: do not touch the landing, terms, privacy or placeholder routes

## Definition of done
- [ ] `python app.py` starts without errors, with or without `SPENDLY_SECRET_KEY` set
- [ ] `GET /register` shows the form as before
- [ ] A valid name, email and 8+ character password creates a row in `users` and redirects to `/login`
- [ ] `/login` shows "Account created — please sign in" once; refreshing the page makes it go away
- [ ] The new row's `password_hash` starts with `pbkdf2:sha256` and does not contain the plain password
- [ ] The email is saved trimmed and lowercase (`  Test@Example.COM ` → `test@example.com`)
- [ ] Registering `demo@spendly.com` again shows "An account with this email already exists." and the row count does not change
- [ ] Blank name, invalid email, or a 7-character password each show the matching error, keep the name and email typed in, and insert nothing
- [ ] Submitting a form that skips browser checks (e.g. with `curl -d`) is still checked on the server
- [ ] The error and success messages use CSS variables only (no hex values added to `style.css`)
