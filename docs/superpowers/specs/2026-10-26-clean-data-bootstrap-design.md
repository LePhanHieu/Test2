# Clean data bootstrap (Phase A) — Design

## Goal and selected approach

DermaScan AI will use a fresh SQLite file for new operational data while the
existing tracked demo SQLite file and all existing assets remain untouched.
Approach A is selected because cleaning mixed records and foreign keys in the
old file (approach B) has unnecessary deletion risk.

## Behavior

- Default database path changes to instance/dermascan_live.db. An explicit
  DATABASE_URL still overrides the default. Schema migrations run before a
  new app is launched.
- A one-time CLI setup asks the local operator for real names, emails and
  passwords for exactly one ADMIN, one DOCTOR and one USER. Passwords are
  hidden in the terminal, hashed, never logged and never hardcoded.
- These three owner-provisioned accounts are activated during setup (not
  public registration); existing public verification via Terminal remains.
- No demo case, analysis, image or patient is inserted into the new database.
- The setup inserts site settings and two banner records pointing at the
  current assets/demoslide1.png and assets/demoslide2.png; the logo and
  favicon fallback keep assets/dermascan_logo.png.
- Bootstrap is transactional and refuses to replace or modify a database
  that already has users. A rerun on a previously provisioned database is
  safe and needs no credentials.
- The browser never creates local fake accounts, stores passwords in
  localStorage, or treats a failed server registration as successful.
- Verification uses an isolated test database and checks fresh setup,
  rerun protection, role/password handling and preserved assets.

## Explicitly deferred by the user

- SMTP delivery of email verification, 2FA OTP and password reset. The
  current Terminal OTP mechanism remains, so this is suitable for local
  supervised use only.
- Removing existing DB files, uploads or reports from Git and rewriting
  repository history. Existing tracked data must not be modified in this
  branch; patient information must not be uploaded in the new commits.
- Deployment, model retraining, migration to PostgreSQL or merge to main.

## Safety and constraints

- No changes to main; push changes only to feature/real-data-bootstrap.
- Keep compatibility with existing Flask-SQLAlchemy and Flask-Migrate APIs.
- No destructive cleanup of old data and no fixed login credentials in docs.
- This phase is not approval to handle identifiable clinical patient data
  on a public website while deferred privacy work remains outstanding.
