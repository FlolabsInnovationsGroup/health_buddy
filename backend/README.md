# Backend

Django + Django REST Framework + PostgreSQL. See the repository README for the architecture.

## Run it locally

From the repository root, copy the environment file and set a secret key:

```powershell
Copy-Item .env.example .env        # bash: cp .env.example .env
```

Start PostgreSQL (needs Docker), then set up Python from the `backend` folder:

```powershell
docker compose up -d db
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1         # bash: source .venv/bin/activate
pip install -r requirements/development.txt
python -m pytest
python manage.py runserver
```

Check it: <http://127.0.0.1:8000/health/> (process is up) and
<http://127.0.0.1:8000/health/db/> (database is reachable).

## Do not run `migrate` yet

The custom user model arrives with the identity app. Django cannot switch user models
after the first migration, so keep your local database un-migrated until that lands.
Tests are safe: they build and drop their own `test_` database.

## Settings

`config.settings.development` is the default for `manage.py` and tests.
`wsgi.py` and `asgi.py` default to `config.settings.production`, which requires
`DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS` and `DATABASE_URL` to be set.
