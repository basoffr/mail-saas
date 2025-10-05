🔍 PROMPT — Backend Completeness & Auto-Fix (FastAPI)

Gebruik Sonnet 4.5 Thinking. Werk incrementeel (atomic commits per fix).
Lees minimaal: backend/app/api/*, backend/app/services/*, backend/app/schemas/*, backend/app/models/*, backend/app/core/* en de frontend service calls (types) waar beschikbaar.

🎯 Doelen

Controleren of alle vereiste endpoints, responses en services aanwezig zijn.

Auto-fix: missende routes/schemas/services implementeren met tests.

I/O-contract borgen: response shape {data: ..., error: null} of {data: null, error: "..."}.

Performance readiness: correcte queries (liefst views/MV’s), juiste indexes (indien DB nodig vanuit service).

Rooktests (curl/httpx) en minimale API-tests toevoegen.

✅ Scope (must-have API’s)

Check en fix per module. Houd dezelfde URL-paden en JSON-shapes aan.

1) Leads

GET /leads (paginatie + zoek/filters/sort)

GET /leads/{id}

POST /import/leads (xlsx/csv → {inserted,updated,skipped,jobId})

GET /assets/image-by-key?key=... → {url}
Te valideren/implementeren

Query-laag respecteert filters (status, domain_tld, has_image, has_var) en zoek (email/bedrijf/domein).

Response shape strikt {data, error}.

Import: mapping + duplicate detectie + progress (mocked job store OK).

Services: leads_service.py bevat functies voor list/detail/import; image resolver.

2) Campaigns

GET /campaigns

POST /campaigns (payload incl. audience filter/lead_ids, schedule, domains, followup)

GET /campaigns/{id}

POST /campaigns/{id}/pause|resume|stop

(bij voorkeur) POST /campaigns/{id}/dry-run
Te valideren/implementeren

Doelgroepselectie: is_complete, suppressions/bounces, “contacted last N days”, one-per-domain.

Unieke (campaign_id, lead_id) enforced door service (en DB).

Dry-run simuleert throttling/venster en retourneert {byDay:[{date,planned}]}.

Services: campaigns_service.py + planning/helpers.

3) Templates

GET /templates

GET /templates/{id}

GET /templates/{id}/preview?lead_id=... → {html,text,warnings?}

POST /templates/{id}/testsend
Te valideren/implementeren

Renderer combineert lead.*, vars.*, campaign.*, image.cid/url.

Warnings bij missende variabelen/afbeeldingen.

Tests: preview zonder/ met lead; testsend validatie.

4) Reports

GET /reports (filters/paginatie)

POST /reports/upload (single)

POST /reports/bulk?mode=by_image_key|by_email

POST /reports/bind / POST /reports/unbind

GET /reports/{id}/download
Te valideren/implementeren

ZIP-bulks: mapping algos (by_image_key/by_email) + resultreport.

Lead drawer indicator has_report (via query of view).

Services: reports_service.py + storage helpers (signed URLs).

5) Stats

GET /stats/summary

GET /stats/export?scope=global|domain|campaign
Te valideren/implementeren

Leest uit DB-views/MV’s (indien aanwezig); zo niet: efficiënte queries met index hints.

CSV export met juiste kolommen; geen O(n) over de hele dataset.

6) Settings

GET /settings

POST /settings (partial update)
Te valideren/implementeren

Singleton-patroon (in service enforced).

Alleen toegestane velden bewerkbaar; read-only blijft read-only.

🔧 Te bouwen/aanpassen (algemene eisen)

Routers in backend/app/api/… met duidelijke @router.get/post en tags.

Schemas (pydantic) voor alle payloads/responses; één generieke ApiResponse[T] helper is plus.

Services per domein; geen DB-logica in routers.

Error handling: central exception handler → altijd {data:null, error:"..."} met correcte HTTP status.

Auth: Supabase JWT decode/validate middleware; alle routes (behalve tracking/unsubscribe) achter auth.

Logging: gestructureerde JSON logs (actie, ids, status, foutmelding).

Tests: httpx/pytest voor routes + unit tests op services (happy + error pad).

🧪 Controle- en Fix-stappen (uit te voeren in volgorde)

Endpoint-inventarisatie

Parse alle @router definities → lijst met paden/methodes.

Vergelijk tegen de Scope hierboven.

Markeer ontbrekende endpoints (diff).

Response-shape audit

Grep naar return in routers/services.

Corrigeer overal naar {data, error}.

Voeg globale exception handler toe (Starlette/FastAPI middleware).

Schemas & Types

Controleer dat elke route een request/response-schema heeft.

Genereer/actualiseer openapi.json; check dat velden kloppen.

Service-laag parity

Voor elke router call moet een servicefunctie bestaan.

Als ontbreekt: implementeren (met duidelijke signatuur, docstring, type hints).

Query’s: efficiënt; bij Stats voorkeur lees uit views/MV (config-vlag als fallback).

Businessregels (per module)

Leads: filters/zoek/sort; import pipeline met duplicate detectie; image resolver.

Campaigns: doelgroep/dedupe/dry-run; status overgangen (pause/resume/stop) met validatie.

Templates: preview renderer + warnings; testsend validatie.

Reports: upload/bulk/bind/unbind; mapping resultaten; signed download.

Stats: snelle summary/export; geen zware runtime aggregatie.

Settings: partial update met veld-whitelist.

Auth & Permissions

JWT check in dependency (e.g., get_current_user()).

Test: requests zonder/ met token.

Observability

JSON-logs voor alle mutaties (ids, status, duration).

Foutcodes/trace bij exceptions.

Smoketests (automatisch)

Voeg scripts/smoke_backend.sh toe met curl-calls:

/leads, /import/leads (multipart), /campaigns POST, /templates, /templates/{id}/preview, /reports (en 1 upload), /stats/summary, /settings.

Exit non-zero bij mismatch op {data, error} of HTTP status.

API-tests (pytest + httpx)

Minimaal 1 happy+1 error test per route.

Fixtures voor sample payloads en auth.

Documenteer

Update README sectie “Backend Endpoints”.

Korte migration notes als er DB-assumpties zijn (bv. views/MV namen).

🧩 Acceptatiecriteria (per module)

Leads: filter/zoek/sort werken; import retourneert {inserted,updated,skipped,jobId}; image-resolver geeft {url}.

Campaigns: create werkt met audience (ids of filter); pause/resume/stop statusflow correct; dry-run geeft {byDay}.

Templates: preview geeft {html,text,warnings?}; testsend valideert email.

Reports: upload/bulk/bind/unbind ronden af met duidelijke foutmeldingen; download levert bestand/signed URL.

Stats: summary < 200ms op sampledata; export levert CSV.

Settings: GET/POST ok; alleen bewerkbare velden wijzigen; singleton enforced in service.

Overal: response-shape consistent; 2xx bij succes, 4xx/5xx bij fout, met {data:null,error:"…"}.

🧱 Output & Artefacten (die ik verwacht)

Diff-rapport met: ontbrekende endpoints → gefixed/gewijzigde bestanden.

Nieuwe/gewijzigde bestanden in api/, services/, schemas/, core/ (error handler/auth).

scripts/smoke_backend.sh (uitvoerbaar).

Testresultaten (pytest -q) groen.

Korte CHANGES.md met lijst fixes.

🔁 Werkstijl & Kwaliteit

Atomic PR’s per domein (Leads → Campaigns → Templates → Reports → Stats → Settings).

Type hints, docstrings, formatter (black/isort), lints clean.

Geen breaking changes aan bestaande route-paden of payload keys.

Bonus (optioneel, als tijd het toelaat)

Config-flag: use_db_views_for_stats=true (fallback naar service-aggregatie in dev).

Kleine helper: generieke ok(data) en fail(message) response builder.