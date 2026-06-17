# Estate — Property Rental Management System

**Version 2.0** — Authentication

Building on the core CRUD foundation, this version adds secure access.
Users now sign up and log in, passwords are hashed, and every property is
tied to the owner who created it.

## What's new in v2
- JWT-based authentication (signup / login)
- Passwords hashed with bcrypt — never stored in plain text
- Protected API routes (Bearer token required)
- Per-user data isolation — owners only see their own properties

## Carried over from v1
- FastAPI + SQLite backend with full property CRUD
- HTML/CSS frontend

## Stack
- Backend: Python, FastAPI, SQLAlchemy
- Auth: JWT (python-jose), bcrypt (passlib)
- Database: SQLite
- Frontend: HTML + CSS

## Run it
```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
uvicorn main:app --reload
```
Open http://127.0.0.1:8000 and create an account.

## Roadmap
- v3 — Image upload & redesigned dashboard
- v4 — Tenants, agreements & payment records