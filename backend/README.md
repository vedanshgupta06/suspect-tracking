# Backend — Suspect Tracking & Crime Analysis System

FastAPI + SQLAlchemy. SQLite by default; point DATABASE_URL at Postgres for the final submission.
Expects sibling folders `../face_ml` and `../fir_ml` (paths configurable in `.env`).

## Setup
    pip install -r requirements.txt
    pip install -r ../face_ml/requirements.txt
    pip install -r ../fir_ml/requirements.txt
    copy .env.example .env
    python seed.py
    uvicorn app.main:app --reload

Open http://127.0.0.1:8000/docs for interactive Swagger UI — try every endpoint from there.

## Default accounts (from seed.py)
| username  | password    | role    |
|-----------|-------------|---------|
| admin     | admin123    | admin   |
| officer1  | police123   | police  |
| judge1    | court123    | court   |
| jailer1   | custody123  | custody |

## Flow
1. `POST /auth/login` -> bearer token. Send it as `Authorization: Bearer <token>` on every other call.
2. `POST /suspects` (police only, multipart: name, alias, photo) -> stores suspect, runs face
   matching against everyone already in the DB, returns ranked alias/repeat-offender candidates.
3. `PATCH /suspects/{id}/status` (police/court/custody) -> add a lifecycle event
   (arrested -> remand -> chargesheet_filed -> trial -> convicted/acquitted -> custody -> released).
4. `POST /cases` (police only) -> files an FIR, runs MO-similarity search against existing
   unsolved cases, returns ranked linked-case suggestions.
5. `GET /dashboard/summary` -> counts for the main dashboard screen.

Thresholds (`FACE_MATCH_THRESHOLD`, `FIR_LINK_THRESHOLD`) are in `.env` — set them to whatever
`face_ml/evaluate.py` and `fir_ml/evaluate_fir.py` found best on the validation split.

Auth is deliberately simple (PBKDF2 password hashing + random bearer tokens stored in the DB,
stdlib only) so it installs without trouble on Windows — swap for a real auth provider before
any real deployment.
