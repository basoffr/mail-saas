# 📐 RULES – Coding Conventions & Afspraken

## 🖥️ Taal & Frameworks
- **Backend**: Python 3.11+, **FastAPI** voor API.
- **Database**: Postgres (via Supabase), ORM: **SQLAlchemy/SQLModel**.
- **Frontend**: React (Next.js, TypeScript), Tailwind + shadcn/ui (gegenereerd met Lovable).
- **Queue/Scheduler**: MVP zonder Redis → Postgres + APScheduler. Later uitbreidbaar naar Celery/Redis.
- **Infra**: Vercel (frontend), Render (backend), Supabase (DB + Storage).

## 📦 Structuur backend
```
backend/
  app/
    main.py (FastAPI entrypoint)
    api/ (routers per domein: leads, campaigns, templates, reports, stats, settings)
    models/ (SQLModel tabellen)
    schemas/ (Pydantic schemas)
    services/ (business logic, mailer, storage)
    workers/ (scheduler, background tasks)
    core/ (config, logging, security)
```

## 🔗 API conventies
- RESTful endpoints, JSON responses.
- **Response shape** altijd `{data: ..., error: null}` of `{data: null, error: "message"}`.
- HTTP statuscodes:
  - 200 OK → success
  - 201 Created → bij POST create
  - 400 Bad Request → validatiefout
  - 404 Not Found
  - 500 Server Error
- Query params gebruiken snake_case.
- Tijdzone: **Europe/Amsterdam**.

## 🗄️ Database conventies
- Tabellen: meervoud (leads, campaigns, messages).
- Kolommen: snake_case.
- Primary key: `id` (UUID v4).
- Timestamps: `created_at`, `updated_at` (UTC, default now()).
- Unieke constraints: email in leads, combinatie (campaign_id + lead_id) in messages.
- Foreign keys met `ON DELETE CASCADE` waar logisch.

## ✉️ E-mail
- Initieel via **SMTP (Vimexx)**.
- Later providers: Postmark of AWS SES.
- Alle mails bevatten **List-Unsubscribe header** (mailto + URL).
- **Opens**: 1×1 pixel (`/track/open.gif?m=...`).
- **Suppressions**: unsubscribes + hard bounces → niet opnieuw mailen.
- Follow-ups: aparte geplande message entries.

## 🧪 Testing
- Unit tests per service.
- API tests met pytest + httpx.
- Fixtures voor DB + mock SMTP.
- Coverage target MVP: 60% (uitbreidbaar later).

## 📝 Logging
- Structured JSON logs.
- Niveau: INFO (prod), DEBUG (dev).
- Log per mail: id, status, domein, error (indien van toepassing).

## 🔐 Security
- Auth via Supabase JWT tokens.
- Alle endpoints (behalve tracking/unsubscribe) → auth verplicht.
- CORS: alleen frontend domain(s).
- Secrets via environment variables.

## 🤝 Afspraken
- Code altijd formatteren met **black** (Python) en **prettier** (frontend).
- Type hints verplicht in Python.
- PR’s via feature branches, squash merge.
- Documentatie up-to-date houden (API.md, SCHEMA.md).

---
© 2025 – Private Mail SaaS