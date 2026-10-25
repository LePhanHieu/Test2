# Clean Data Bootstrap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace demo-first startup with a new empty SQLite database, three local owner-provisioned accounts and preserved existing brand assets.

**Architecture:** Flask-Migrate owns schema creation; a standalone Click CLI command owns one-time account/content provisioning. Existing API routes remain the source of truth for browser authentication. Keep all old database/media files unchanged.

**Tech Stack:** Python, Flask 3.1, Flask-SQLAlchemy, Flask-Migrate, Click, SQLite, JavaScript.

**Spec:** docs/superpowers/specs/2026-10-26-clean-data-bootstrap-design.md

## Global Constraints

- No modifications to main; push only feature/real-data-bootstrap.
- Defer SMTP email/OTP and Git history/data separation.
- Preserve existing assets and old SQLite files unchanged.
- Do not hardcode or print passwords, and do not persist raw passwords in browser storage.

## Review Focus

- Duplicate email across bootstrap roles must rollback entirely (Task 1).
- Setup against a populated preexisting database must not replace users (Task 1).
- A fresh database must initialize to zero demo cases and two valid active banners (Task 1).
- Invalid or absent CSRF/network responses must not create a browser-only account (Task 3).
- Startup migration/bootstrap failures must prevent launching an uninitialized app (Task 2).

---

### Task 1: One-time real account and brand content setup

**Files:**
- Create: skin_cancer/webapp/initial_setup.py
- Modify: skin_cancer/webapp/database_app.py
- Test: tests/test_initial_setup.py

**Interfaces:**
- register_initial_setup(app) registers a `setup-initial` Click command.
- provision_initial_data(accounts) inserts exactly ADMIN/DOCTOR/USER and two slides in one transaction.

- [ ] Write failing tests for empty SQLite setup, hashed credentials, initial three roles, two active slides, rerun and duplicate emails.
- [ ] Run the targeted test and confirm expected failure.
- [ ] Implement small Click prompts and transactional provisioning with refuse-on-existing-users behavior.
- [ ] Run targeted tests; confirm success; commit task.

### Task 2: New default SQLite and demo-free launcher

**Files:**
- Modify: skin_cancer/webapp/config.py
- Modify: .env.example
- Modify: run_app.bat
- Modify: README_PHASE1.md
- Test: tests/test_bootstrap_configuration.py

**Interfaces:**
- Config defaults to instance/dermascan_live.db and still honors DATABASE_URL.
- `run_app.bat` runs `db upgrade`, then `setup-initial`, then the web app and aborts on errors.

- [ ] Write failing tests for defaults and launcher contract, including absence of seed-demo.
- [ ] Run targeted tests to confirm failure.
- [ ] Change configuration, launch script and local setup instructions.
- [ ] Run targeted tests; confirm success; commit task.

### Task 3: Remove browser-only demo authentication

**Files:**
- Modify: skin_cancer/webapp/templates/index.html
- Test: tests/test_auth_template.py

**Interfaces:**
- Registration and login use `/api/auth/register` and `/api/auth/login` exclusively.
- No local users, fake session, or plaintext password persistence.

- [ ] Write failing static/behavioral contract tests proving local demo user and password storage are absent.
- [ ] Run targeted tests to confirm failure.
- [ ] Remove local fake user/session fallback and the displayed demo login; keep theme preference storage.
- [ ] Run targeted tests; confirm success; commit task.

### Task 4: End-to-end verification and branch publishing

**Files:**
- Check: all changed files, git diff and tests.

- [ ] Run syntax validation and isolated suite; run full available suite or identify its unavailable dependencies.
- [ ] Inspect git status/diff for tracked media, database files and inadvertent credentials.
- [ ] Commit documentation and any remaining source changes.
- [ ] Push only feature/real-data-bootstrap; verify remote branch exists and main SHA unchanged.
