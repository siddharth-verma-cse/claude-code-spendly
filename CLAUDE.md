# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Spendly is a personal expense tracker built with Flask + Jinja templates + vanilla JS/CSS, developed as a step-by-step learning project. Many pieces are intentional stubs that get filled in by numbered "Steps" (e.g. Step 1 database setup, Step 3 logout, Step 7–9 expense CRUD). When implementing a step, replace the placeholder rather than building around it.

## Commands

The project uses a local virtualenv at `venv/` (Python 3.9).

```bash
source venv/bin/activate
pip install -r requirements.txt
python app.py              # dev server with debug reload on http://localhost:5001
pytest                     # run tests (pytest + pytest-flask installed; no tests exist yet)
pytest path/to/test_file.py::test_name   # run a single test
```

There is no linter or build step configured.

## Architecture

- `app.py` — the single Flask app and all routes. Top section has working page routes (`/`, `/register`, `/login`, `/terms`, `/privacy`) that only render templates; the bottom section holds placeholder routes (`/logout`, `/profile`, `/expenses/add`, `/expenses/<id>/edit`, `/expenses/<id>/delete`) that return "coming in Step N" strings. No auth, sessions, or form handling exists yet.
- `database/db.py` — currently a stub. Intended contract (from its header comment): `get_db()` returns a SQLite connection with `row_factory` set and foreign keys enabled; `init_db()` creates tables with `CREATE TABLE IF NOT EXISTS`; `seed_db()` inserts dev sample data. The SQLite file `expense_tracker.db` is git-ignored.
- `templates/base.html` — shared layout (navbar, footer with Terms/Privacy links, Google Fonts DM Serif Display + DM Sans, `static/css/style.css`, `static/js/main.js`). All pages `{% extends "base.html" %}` and use blocks `title`, `head` (page-specific CSS), `content`, and `scripts` (page-specific JS).
- `static/css/style.css` holds global styles; `static/css/landing.css` is loaded only by `landing.html` via the `head` block. Legal pages (`terms.html`, `privacy.html`) share a `legal-block` structure — keep new content pages consistent with them.
- No JS framework: page JS is vanilla, written inline in a template's `scripts` block (e.g. the YouTube modal on the landing page) or in `static/js/main.js`.

## Conventions

- Currency/copy is India-focused ("Track every rupee").
- Commit messages are prefixed by area, e.g. `landing: add privacy policy page and route`.
- Changes are typically scoped narrowly ("modify only the hero section", "do not modify anything else") — don't touch unrelated parts of a template or stylesheet.
- The user runs shell and git commands themselves; suggest the exact command rather than executing it.
