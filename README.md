# Estate — Property Rental Management System

A FastAPI + SQLite + JWT application for property owners to manage rental
properties, with full CRUD, image upload, and a clean HTML/CSS frontend.

## Stack
- **Backend:** Python, FastAPI, SQLAlchemy
- **Database:** SQLite (`rental.db`, created automatically)
- **Auth:** JWT (signup / login, Bearer tokens)
- **Frontend:** HTML + CSS (Bricolage Grotesque + Inter), minimal vanilla JS
- **Images:** uploaded to `static/uploads/`

## Project structure
```
property-rental/
├── main.py            # FastAPI app: auth, CRUD, upload, page routes, demo seed
├── database.py        # SQLite + SQLAlchemy setup
├── models.py          # User, Property
├── schemas.py         # Pydantic request/response models
├── auth.py            # password hashing + JWT
├── requirements.txt
├── frontend/
│   ├── login.html
│   ├── signup.html
│   ├── index.html     # dashboard + property gallery
│   ├── create.html    # add property
│   └── update.html    # edit property
└── static/
    ├── style.css
    ├── app.js         # shared auth + fetch helpers
    └── uploads/       # uploaded images land here
```

## Run it
```bash
cd property-rental
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```
Open http://127.0.0.1:8000

**Demo login:** `demo@rental.app` / `demo1234` (comes with 4 sample properties),
or create your own account on the sign-up page.

## API (all property routes require a Bearer token)
| Method | Route                      | Action            |
|--------|----------------------------|-------------------|
| POST   | `/api/signup`              | Register          |
| POST   | `/api/login`               | Log in, get token |
| GET    | `/api/me`                  | Current user      |
| POST   | `/api/upload`              | Upload an image   |
| GET    | `/api/properties`          | List (own)        |
| GET    | `/api/properties/{id}`     | Read one          |
| POST   | `/api/properties`          | Create            |
| PUT    | `/api/properties/{id}`     | Update            |
| DELETE | `/api/properties/{id}`     | Delete            |

Interactive API docs are available at http://127.0.0.1:8000/docs

## Notes
- Each user only sees and edits their own properties.
- Change `SECRET_KEY` in `auth.py` before deploying anywhere real.
- The schema extends cleanly to tenants, agreements, and payments if you want
  to grow it into the full brief later.
```
