# Running Revinteq Locally on Your Laptop

## What You Need Installed

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.11 or 3.12 | python.org |
| Node.js | 18 or 20 | nodejs.org |
| VS Code | Any | code.visualstudio.com |

**That is it. No MySQL, no Redis, no Docker needed.**

---

## Step 1 — Backend Setup

Open a terminal in VS Code, navigate to the `backend/` folder:

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate          # Mac / Linux
venv\Scripts\activate             # Windows

# Install packages (local version — no MySQL client)
pip install -r requirements-local.txt

# Create the database (SQLite — creates a local db.sqlite3 file)
python manage.py migrate --settings=config.settings.local

# Create your admin user
python manage.py createsuperuser --settings=config.settings.local

# Start the backend
python manage.py runserver --settings=config.settings.local
```

Backend is now running at **http://localhost:8000**

---

## Step 2 — Frontend Setup

Open a second terminal in VS Code, navigate to the `frontend/` folder:

```bash
cd frontend

# Install Node packages
npm install

# Start the frontend
npm run dev
```

Frontend is now running at **http://localhost:5173**

---

## URLs

| What | URL |
|------|-----|
| App (client portal) | http://localhost:5173 |
| Login | http://localhost:5173/login |
| Admin login | http://localhost:5173/admin/login |
| Django admin panel | http://localhost:8000/admin/ |
| API documentation | http://localhost:8000/api/docs/ |
| API root | http://localhost:8000/api/v1/ |

---

## VS Code Tips

Install these extensions for the best experience:

- **Python** (Microsoft) — Django syntax, debugging
- **Pylance** — Python intellisense
- **Vue - Official** (Vuejs) — Vue 3 syntax highlighting
- **Tailwind CSS IntelliSense** — autocomplete for Tailwind classes
- **Django** (batisteo) — template syntax highlighting

---

## Recommended VS Code workspace settings

Create `.vscode/settings.json` in the project root:

```json
{
  "python.defaultInterpreterPath": "./backend/venv/bin/python",
  "python.terminal.activateEnvironment": true,
  "[python]": {
    "editor.formatOnSave": true
  },
  "[vue]": {
    "editor.defaultFormatter": "Vue.volar"
  },
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    "**/node_modules": true,
    "backend/db.sqlite3": false
  }
}
```

---

## How to Reset the Database

```bash
cd backend
rm db.sqlite3
python manage.py migrate --settings=config.settings.local
python manage.py createsuperuser --settings=config.settings.local
```

---

## Common Errors and Fixes

**Error:** `ModuleNotFoundError: No module named 'mysqlclient'`
**Fix:** You're using the wrong requirements file. Run:
```bash
pip install -r requirements-local.txt
```

**Error:** `django.core.exceptions.ImproperlyConfigured: The SECRET_KEY setting must not be empty`
**Fix:** You forgot `--settings=config.settings.local`. Either add it to every command or set it once:
```bash
export DJANGO_SETTINGS_MODULE=config.settings.local
# Now you can just run: python manage.py runserver
```

**Error:** `CORS error` in browser when frontend calls backend
**Fix:** Make sure backend is running on port 8000 and frontend on port 5173. The Vite dev server proxies all `/api` calls automatically.

**Error:** `No such table: tenants_tenant`
**Fix:** Migrations haven't run yet:
```bash
python manage.py migrate --settings=config.settings.local
```

**Error:** Vue page shows `401 Unauthorized`
**Fix:** You need to log in first. Go to http://localhost:5173/login and use the credentials from `createsuperuser`.

---

## Setting DJANGO_SETTINGS_MODULE Permanently in VS Code

Add this to your VS Code terminal settings so you never need `--settings=...`:

1. Open VS Code Settings (Ctrl+,)
2. Search for `terminal.integrated.env`  
3. Add to your OS section:
```json
"terminal.integrated.env.osx": {
  "DJANGO_SETTINGS_MODULE": "config.settings.local"
},
"terminal.integrated.env.linux": {
  "DJANGO_SETTINGS_MODULE": "config.settings.local"
},
"terminal.integrated.env.windows": {
  "DJANGO_SETTINGS_MODULE": "config.settings.local"
}
```
