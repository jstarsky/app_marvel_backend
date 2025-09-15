
```
app_marvel_backend/
│
├── requirements.txt
├── requirements-dev.txt
├── manage.py
├── .env.example
├── .gitignore
├── pytest.ini
├── db.sqlite3  # SQLite database file
│
├── app_marvel_backend/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
# app_marvel_backend
```

Small Django REST API project for authentication.

This README explains how to set up, run, and exercise the main authentication routes.

---

## Requirements

- Python 3.8+
- pip
- (optional) virtualenv / venv

## Quick setup (macOS / zsh)

1. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. (Optional) Create a `.env` file next to `manage.py` and set any environment variables you need. Example:

```env
SECRET_KEY=change-me
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
```

4. Run migrations and create a superuser (if needed):

```bash
python manage.py migrate
python manage.py createsuperuser
```

5. Start the development server:

```bash
python manage.py runserver
```

Server will be available at http://127.0.0.1:8000

---

## API routes (authentication app)

All paths below are relative to `/api/auth/` (adjust if you mounted the app differently):

- POST /login/ — Obtain access token (returns `data.token`) and user data
- POST /register/ — Register a new user (requires `username`, `password`, `password_confirm`)
- POST /logout/ — Global logout (requires `Authorization: Bearer <access_token>`) — blacklists refresh tokens
- GET  /profile/ — Get current user profile (requires `Authorization: Bearer <access_token>`)
- PUT/PATCH /profile/update/ — Update profile (requires auth)
- POST /change-password/ — Change password (requires auth)
- POST /token/refresh/ — Refresh access token (standard SimpleJWT endpoint)

Note: routes and exact response shapes follow the current codebase. The project uses a small success wrapper for successful responses.

---

## Example responses

Successful wrapper shape:

```json
{
    "success": true,
    "data": { /* endpoint-specific payload */ }
}
```

Error wrapper shape:

```json
{
    "success": false,
    "message": "Error message",
    "errors": { /* optional field errors */ }
}
```

---

## Quick curl examples

1) Register

```bash
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
    -H "Content-Type: application/json" \
    -d '{"username":"alice","password":"secret12","password_confirm":"secret12"}'
```

2) Login

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
    -H "Content-Type: application/json" \
    -d '{"username":"alice","password":"secret12"}'
```

Response contains `data.token` which you should use as the Bearer token.

3) Get profile

```bash
curl -X GET http://127.0.0.1:8000/api/auth/profile/ \
    -H "Authorization: Bearer <ACCESS_TOKEN>"
```

4) Logout (no body required)

```bash
curl -X POST http://127.0.0.1:8000/api/auth/logout/ \
    -H "Authorization: Bearer <ACCESS_TOKEN>"
```

---

## Password rules

- Minimum length: 6
- Maximum length: 8
- Common-password check removed (project currently allows common passwords)

These rules are enforced by Django password validators configured in `settings.py`.

---

## Troubleshooting

- If you see an error about OutstandingToken/BlacklistedToken, ensure `rest_framework_simplejwt.token_blacklist` is in `INSTALLED_APPS` and run `python manage.py migrate`.
- If `python manage.py` fails, ensure your virtualenv is activated and Python is the correct interpreter.

---

## Deployment / Railway notes

When deploying to Railway (or any host) and using a separate frontend (Next.js/React), set these environment variables so CORS and cookie behavior work correctly:

- `CORS_ALLOWED_ORIGINS` — comma-separated list of allowed origins. Example for local dev and a deployed frontend:
    - `http://localhost:3000,https://your-frontend.up.railway.app`

- `SESSION_COOKIE_SECURE` — set to `true` in production when using HTTPS. (Default `false` for local dev.)
- `CSRF_COOKIE_SECURE` — set to `true` in production when using HTTPS. (Default `false` for local dev.)

Examples on Railway (set these in the project Environment variables):

```
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://your-frontend.up.railway.app
SESSION_COOKIE_SECURE=true
CSRF_COOKIE_SECURE=true
DEBUG=False
```

Also ensure you run migrations during deployment so the token blacklist tables exist:

```
python manage.py migrate
```

If you prefer not to use server-side token blacklisting, remove `'rest_framework_simplejwt.token_blacklist'` from `INSTALLED_APPS` and avoid using blacklist API calls; logout will be client-side only.

## Preflight test with curl

To verify the backend responds to CORS preflight correctly (important when using credentials), run this OPTIONS request from a shell and check the response headers:

```bash
curl -i -X OPTIONS 'https://appmarvelbackend-production.up.railway.app/auth/login/' \
    -H 'Origin: http://localhost:3000' \
    -H 'Access-Control-Request-Method: POST' \
    -H 'Access-Control-Request-Headers: content-type'
```

Expected headers (when configured correctly):

- Access-Control-Allow-Origin: http://localhost:3000
- Access-Control-Allow-Credentials: true
- Access-Control-Allow-Methods: DELETE, GET, OPTIONS, PATCH, POST, PUT
- Access-Control-Allow-Headers: content-type, authorization, x-csrftoken

If you still see `Access-Control-Allow-Origin: *` or `Access-Control-Allow-Credentials` missing, redeploy after ensuring the `CORS_ALLOWED_ORIGINS` env var is set and the latest code is active.