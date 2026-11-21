# LeakyCart

A small Flask + Supabase shop that is deliberately full of security bugs. It exists only as a test fixture for a security scanner. Do not deploy it, and every key in it is fake.

## Files

| File | Role |
|---|---|
| `app.py` | Flask API (orders, login, admin, integrations) |
| `requirements.txt` | Python dependencies |
| `schema.sql` | Supabase/Postgres tables and RLS policies |
| `.env` | Committed environment file |
| `dist/bundle.js` | Pre-built browser bundle |

## Planted bugs, by scanner layer

| # | Layer | What is planted | Where |
|---|---|---|---|
| 1 | Secrets | Live-looking Stripe key `sk_live_...` | `app.py`, `.env`, `dist/bundle.js` |
| 1 | Secrets | JWT with `role: service_role` (critical) | `.env`, `dist/bundle.js` |
| 1 | Secrets | JWT with `role: anon` (should be ignored) | `.env`, `dist/bundle.js` |
| 1 | Secrets | `your_openai_api_key_here` (placeholder filter should skip) | `.env` |
| 1 | Secrets | Hardcoded Flask `secret_key`, DB password in `DATABASE_URL` | `app.py`, `.env` |
| 2 | Code patterns | String-built SQL (`%` formatting, f-string, concatenation) | `app.py` register, login, search_orders |
| 2 | Code patterns | `subprocess.run(..., shell=True)` with user input | `app.py` diagnose |
| 2 | Code patterns | `debug=True` on `0.0.0.0` | `app.py` main |
| 2 | Code patterns | `requests.get(..., verify=False)` plus SSRF via user URL | `app.py` shipping_rate |
| 2 | Code patterns | Auth only in `before_request`, none on routes | `app.py` require_login |
| 2 | Code patterns | `yaml.load` with `Loader`, `pickle.loads` on request data, MD5 passwords | `app.py` |
| 3 | Dependencies | Known-vulnerable versions: Flask 1.1.2, Werkzeug 0.15.3, Jinja2 2.10, PyYAML 5.3, requests 2.19.1, urllib3 1.24.1, Pillow 8.2.0, flask-cors 3.0.8 | `requirements.txt` |
| 4 | Fake packages | `requets` (typo of requests), `flask-securitykit-pro`, `supabase-auth-helper-utils` (made-up names) | `requirements.txt` |
| 5 | Database policies | `orders`: RLS never enabled | `schema.sql` |
| 5 | Database policies | `profiles`: policy uses `auth.role()` instead of owner check | `schema.sql` |
| 5 | Database policies | `notes`: `using (true)` | `schema.sql` |
| 5 | Database policies | `payments`: permissive policies OR together (`amount > 0` opens it) | `schema.sql` |
| 5 | Database policies | `get_all_orders()` is `SECURITY DEFINER`, no `search_path`, granted to `anon` | `schema.sql` |
| 6 | Config / IaC | Committed `.env` | `.env` |
| 6 | Config / IaC | Service-role key in a `NEXT_PUBLIC_*` variable | `.env` |
| 6 | Config / IaC | Open CORS: `origins="*"` with credentials, and `CORS_ORIGIN=*` | `app.py`, `.env` |
| 7 | Running app (DAST) | Not built yet. Run `python app.py` and point ZAP at `localhost:5000` once ready | n/a |
| 8 | Access-control proof | IDOR: `/orders/<id>` returns any user's order to any logged-in user | `app.py` get_order |
| 8 | Access-control proof | `/admin/*` has no admin check, any logged-in user gets in | `app.py` |
| 9 | Browser bundle | Service-role and Stripe keys embedded, inline source map exposes sources | `dist/bundle.js` |

## Running it

```bash
python -m venv .venv && source .venv/bin/activate
pip install flask==1.1.2 flask-cors==3.0.8 pyyaml requests   # the full requirements.txt will fail on the fake packages, on purpose
python app.py
```

For the access-control probe, register two users, log in as user B, and request an order owned by user A at `/orders/<id>`.
