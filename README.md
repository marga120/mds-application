# MDS Application Management System

A Flask web application for managing Masters of Data Science student applications at UBC. Supports role-based access for Admins, Faculty, and Viewers to process, review, and track applicants across academic sessions.

- **Last updated**: 2/28/2026

---

## Table of Contents

1. [Local Development](#local-development)
2. [Architecture](#architecture)
3. [Project Structure](#project-structure)
4. [API Reference](#api-reference)
5. [User Guide](#user-guide)
6. [Troubleshooting](#troubleshooting)

---

## Local Development

### Prerequisites

- [Python 3.10+](https://www.python.org/downloads/)
- [Node.js 18+](https://nodejs.org/)
- [PostgreSQL](https://www.postgresql.org/download/)

### Setup

```bash
# Clone the repo
git clone <repository-url>
cd mds-application

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt
npm install
```

### Environment Variables

Create a `.env` file in the project root:

```env
HOST=localhost
DATABASE=mds_database
USER=your_postgres_username
PASSWORD=your_postgres_password
PORT=5432
SECRET_KEY=your-secret-key
```

### Create the Database

```sql
CREATE DATABASE mds_database;
```

The schema is applied automatically on first startup — no manual migration needed.

### Run the App

```bash
# Start Flask + Tailwind watch mode together (recommended)
npm run dev

# Flask only
python main.py

# Build CSS once without watching
npm run build-css-once
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

### Test Accounts

Run `python seed.py` to create these accounts (all use password `password`):

| Role    | Email                 |
| ------- | --------------------- |
| Admin   | testuser1@example.com |
| Admin   | testuser2@example.com |
| Faculty | testuser3@example.com |
| Viewer  | testuser4@example.com |

---

## Architecture

The codebase follows a strict four-layer architecture. Each layer has one responsibility and may only depend on layers below it.

```
HTTP Request
    └── API Layer       (api/)       — Route handling, auth checks, request parsing
          └── Service Layer  (services/) — Business logic, orchestration, activity logging
                └── Model Layer  (models/) — SQL queries via db_helpers context managers
                      └── Database  (utils/db_helpers.py + utils/database.py)
```

### Layer Rules

| Layer       | Responsible For                                     | Not Allowed                        |
| ----------- | --------------------------------------------------- | ---------------------------------- |
| `api/`      | Flask routes, permission decorators, JSON responses | SQL, business logic                |
| `services/` | Business logic, validation, calling models, logging | Flask imports, SQL, DB connections |
| `models/`   | SQL via `db_connection` / `db_transaction`          | Flask, business logic              |
| `utils/`    | Shared helpers                                      | Application-specific logic         |

### Database Access Pattern

All database access uses context managers from `utils/db_helpers.py`. Raw `get_db_connection()` is never called directly in models, services, or API files.

```python
from utils.db_helpers import db_connection, db_transaction

# Reads — no commit needed
with db_connection() as (conn, cursor):
    cursor.execute("SELECT * FROM table WHERE id = %s", (id,))
    row = cursor.fetchone()   # Returns a dict (RealDictCursor)

# Writes — auto-commits on success, rolls back on exception
with db_transaction() as (conn, cursor):
    cursor.execute("INSERT INTO table (col) VALUES (%s)", (value,))
```

### Adding a New Feature

**New API endpoint:**

1. Add a route to the appropriate blueprint in `api/`
2. Apply `@login_required` and a permission check
3. Parse and validate request data at the boundary
4. Delegate to a service method — no logic in the controller
5. Return `jsonify({"success": True, ...})`

**New service method:**

1. Add the method to the appropriate class in `services/`
2. Call model functions — no SQL here
3. Call `log_activity(...)` for any mutations
4. Raise `ValueError` for expected failures (bad input, conflicts)

**New model function:**

1. Use `db_connection()` for reads, `db_transaction()` for writes
2. Access row columns by name — all cursors return dicts
3. Return `(result, error_message)` tuples for callers that need error propagation

**New database column:**

1. Add it to `schema.sql`
2. Restart Flask — schema changes are applied automatically
3. Update the model, service, and API as needed

---

## Project Structure

```
mds-application/
├── main.py                          # App entry point, blueprint registration
├── schema.sql                       # Database schema (auto-applied on startup)
├── seed.py                          # Test data seeder
│
├── api/                             # HTTP layer — routes only, no SQL
│   ├── applicants.py                # Applicant CRUD, CSV upload, export
│   ├── auth.py                      # Login, logout, user management
│   ├── database.py                  # DB backup and restore endpoints
│   ├── documents.py                 # Document upload and retrieval
│   ├── logs.py                      # Activity log endpoints
│   ├── ratings.py                   # Faculty ratings
│   ├── sessions.py                  # Academic session management
│   ├── statuses.py                  # Review status configuration
│   └── test_scores.py               # Test score updates
│
├── services/                        # Business logic layer — no Flask, no SQL
│   ├── applicant_service.py
│   ├── auth_service.py
│   ├── csv_import_service.py
│   ├── document_service.py
│   ├── export_service.py
│   ├── log_service.py
│   ├── rating_service.py
│   ├── session_service.py
│   └── status_service.py
│
├── models/                          # Data access layer — SQL only
│   ├── applicants/
│   │   ├── core.py                  # Applicant CRUD queries
│   │   ├── csv_processing.py        # CSV row parsing and DB inserts
│   │   ├── english_status.py        # English proficiency computation
│   │   └── export.py                # XLSX export queries
│   ├── documents.py
│   ├── institutions.py
│   ├── ratings.py
│   ├── sessions.py
│   ├── statuses.py
│   ├── test_scores.py
│   └── users.py
│
├── utils/
│   ├── database.py                  # Connection config, schema init (foundation)
│   ├── db_helpers.py                # db_connection / db_transaction context managers
│   ├── activity_logger.py           # Audit trail logging
│   ├── csv_helpers.py               # CSV response helpers
│   ├── permissions.py               # @require_admin, @require_faculty_or_admin
│   └── test_score_helpers.py        # Generic test score processor
│
├── static/
│   ├── css/
│   │   ├── input.css                # Tailwind source (edit this)
│   │   └── output.css               # Auto-generated (do not edit)
│   └── js/
│       ├── api/
│       │   └── client.js            # Centralized fetch wrapper
│       ├── components/              # Reusable UI components
│       │   ├── data-table.js
│       │   ├── modal.js
│       │   └── notification.js
│       ├── pages/                   # One file per page
│       │   ├── account.js
│       │   ├── create-session.js
│       │   ├── index.js
│       │   ├── login.js
│       │   ├── logs.js
│       │   ├── statistics.js
│       │   ├── statuses.js
│       │   └── users.js
│       ├── services/                # API call wrappers
│       │   ├── applicant-service.js
│       │   ├── auth-service.js
│       │   ├── session-service.js
│       │   └── status-service.js
│       └── utils/
│           ├── constants.js
│           ├── formatters.js
│           └── validators.js
│
└── templates/                       # Jinja2 HTML templates
    ├── index.html
    ├── login.html
    ├── account.html
    ├── users.html
    ├── logs.html
    ├── statistics.html
    ├── status-config.html
    └── create-session.html
```

---

## API Reference

All endpoints require authentication unless marked Public. Responses use `{"success": true/false, ...}`.

### Auth — `/api/auth/`

| Method | Path                | Description         | Role   |
| ------ | ------------------- | ------------------- | ------ |
| POST   | `/login`            | Login               | Public |
| POST   | `/logout`           | Logout              | Any    |
| GET    | `/check-session`    | Session check       | Public |
| GET    | `/user`             | Current user info   | Any    |
| GET    | `/users`            | List all users      | Admin  |
| GET    | `/user/<id>`        | Get user by ID      | Admin  |
| POST   | `/register`         | Create user         | Admin  |
| PUT    | `/user/<id>`        | Update user         | Admin  |
| DELETE | `/delete-user/<id>` | Delete user         | Admin  |
| DELETE | `/delete-users`     | Bulk delete users   | Admin  |
| POST   | `/update-email`     | Change own email    | Any    |
| POST   | `/reset-password`   | Change own password | Any    |

### Applicants — `/api/`

| Method | Path                                                 | Description             | Role          |
| ------ | ---------------------------------------------------- | ----------------------- | ------------- |
| GET    | `/applicants`                                        | List applicants         | Any           |
| POST   | `/upload`                                            | Upload CSV              | Admin         |
| GET    | `/applicant-info/<code>`                             | Personal info           | Any           |
| GET    | `/applicant-test-scores/<code>`                      | Test scores             | Any           |
| GET    | `/applicant-institutions/<code>`                     | Institution history     | Any           |
| GET    | `/applicant-application-info/<code>`                 | Application info        | Any           |
| PUT    | `/applicant-application-info/<code>/status`          | Update review status    | Admin         |
| PUT    | `/applicant-application-info/<code>/prerequisites`   | Update prereqs/GPA      | Admin/Faculty |
| PUT    | `/applicant-application-info/<code>/english-status`  | Update English status   | Admin         |
| PUT    | `/applicant-application-info/<code>/english-comment` | Update English comment  | Admin         |
| PUT    | `/applicant-application-info/<code>/scholarship`     | Update scholarship      | Admin         |
| GET    | `/export/all`                                        | Export all as XLSX      | Admin/Faculty |
| POST   | `/export/selected`                                   | Export selected as XLSX | Admin/Faculty |
| DELETE | `/clear-all-data`                                    | Wipe all applicant data | Admin         |

### Sessions — `/api/`

| Method | Path                     | Description       | Role  |
| ------ | ------------------------ | ----------------- | ----- |
| GET    | `/sessions`              | List all sessions | Any   |
| POST   | `/sessions/create`       | Create session    | Admin |
| PUT    | `/sessions/<id>/archive` | Archive session   | Admin |
| PUT    | `/sessions/<id>/restore` | Restore session   | Admin |

### Ratings — `/api/`

| Method | Path                        | Description               | Role          |
| ------ | --------------------------- | ------------------------- | ------------- |
| GET    | `/ratings/<code>`           | All ratings for applicant | Any           |
| GET    | `/ratings/<code>/my-rating` | Current user's rating     | Any           |
| POST   | `/ratings/<code>`           | Add or update rating      | Admin/Faculty |

### Statuses — `/api/`

| Method | Path                          | Description      | Role  |
| ------ | ----------------------------- | ---------------- | ----- |
| GET    | `/api/statuses`               | Active statuses  | Any   |
| GET    | `/api/admin/statuses`         | All statuses     | Admin |
| POST   | `/api/admin/statuses`         | Create status    | Admin |
| PUT    | `/api/admin/statuses/<id>`    | Update status    | Admin |
| DELETE | `/api/admin/statuses/<id>`    | Delete status    | Admin |
| POST   | `/api/admin/statuses/reorder` | Reorder statuses | Admin |

### Documents — `/api/`

| Method | Path                          | Description            | Role          |
| ------ | ----------------------------- | ---------------------- | ------------- |
| GET    | `/api/documents/<code>`       | List documents         | Any           |
| POST   | `/api/documents/<code>`       | Upload document        | Admin/Faculty |
| GET    | `/api/documents/view/<id>`    | View/download document | Any           |
| DELETE | `/api/documents/<id>`         | Delete document        | Admin         |
| GET    | `/api/documents/count/<code>` | Document count         | Any           |

### Logs — `/api/`

| Method | Path                          | Description    | Role  |
| ------ | ----------------------------- | -------------- | ----- |
| GET    | `/logs`                       | Activity logs  | Admin |
| GET    | `/logs/export/status-changes` | Export log CSV | Admin |

### Database — `/api/`

| Method | Path               | Description      | Role  |
| ------ | ------------------ | ---------------- | ----- |
| POST   | `/database/export` | Export DB backup | Admin |
| POST   | `/database/import` | Import DB backup | Admin |

---

## User Guide

### Roles and Permissions

| Action                      | Admin | Faculty | Viewer |
| --------------------------- | ----- | ------- | ------ |
| View applications           | Yes   | Yes     | Yes    |
| View statistics             | Yes   | Yes     | Yes    |
| Update own email/password   | Yes   | Yes     | Yes    |
| Rate students               | Yes   | Yes     | No     |
| Edit prerequisites          | Yes   | Yes     | No     |
| Upload/delete documents     | Yes   | Yes     | No     |
| Change application status   | Yes   | No      | No     |
| Edit English status/comment | Yes   | No      | No     |
| Upload CSV                  | Yes   | No      | No     |
| Export data                 | Yes   | No      | No     |
| Manage users                | Yes   | No      | No     |
| Create/archive sessions     | Yes   | No      | No     |
| Configure statuses          | Yes   | No      | No     |
| View activity logs          | Yes   | No      | No     |
| Database backup/restore     | Yes   | No      | No     |

### Pages

| URL                   | Description                 | Access |
| --------------------- | --------------------------- | ------ |
| `/`                   | Main applicant list         | All    |
| `/statistics`         | Application analytics       | All    |
| `/account`            | Email and password settings | All    |
| `/users`              | User management             | Admin  |
| `/logs`               | Activity audit log          | Admin  |
| `/status-config`      | Review status configuration | Admin  |
| `/create-new-session` | Create academic session     | Admin  |

---

## Troubleshooting

**Database connection errors**

- Verify PostgreSQL is running: `sudo systemctl status postgresql`
- Double-check credentials in `.env`
- Confirm the database exists: `psql -l`

**CSS not loading**

```bash
npm run build-css-once
```

**Schema changes not applying**

- The schema is applied once on first startup. Drop and recreate the database, then restart Flask.

**CSV upload fails**

- Ensure the file has a `User Code` column
- Verify the user is logged in as Admin
- Check that `Program CODE`, `Program`, and `Session` columns are present

**Permission denied on a route**

- Check the user's role in the database
- Verify `@login_required` and permission decorators on the route

**Debug mode**

```bash
export FLASK_DEBUG=1
python main.py
```

---

## Production Checklist

- Set `SECRET_KEY` to a secure random value in `.env`
- Set `SESSION_COOKIE_SECURE = True` in `main.py` (requires HTTPS)
- Set `debug=False` in `main.py`
- Use a production WSGI server (Gunicorn, uWSGI)
- Configure PostgreSQL connection pooling
- Schedule regular database backups via the admin panel or pg_dump
- Set `MAX_CONTENT_LENGTH` appropriate for your upload needs (default: 30MB)

---

## License

Developed for the University of British Columbia's Masters of Data Science program. All rights reserved.
