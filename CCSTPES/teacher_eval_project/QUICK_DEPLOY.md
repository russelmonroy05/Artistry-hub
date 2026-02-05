# 🚀 Deploy Teacher Evaluation to Render (5 Minutes)

## Copy-Paste Quick Start

### Step 1: Update settings.py MIDDLEWARE (add WhiteNoise)

Add this **as the second item** in your `MIDDLEWARE` list in `settings.py`:

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ADD THIS
    'django.contrib.sessions.middleware.SessionMiddleware',
    # ... rest of middleware ...
]
```

### Step 2: Create files in your project root

**File: `Procfile`** (no extension)

```
web: gunicorn teacher_eval_project.wsgi:application --log-file -
```

**File: `render.yaml`**

```yaml
databases:
  - name: postgresdb
    plan: free
    ipAllowList: []

services:
  - type: web
    name: teacher-eval
    runtime: python
    buildCommand: pip install -q -r requirements.txt && python manage.py migrate && python manage.py collectstatic --no-input
    startCommand: gunicorn teacher_eval_project.wsgi:application
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.6
      - key: DEBUG
        value: "False"
```

### Step 3: Push to GitHub

```bash
git add .
git commit -m "Add deployment files"
git push
```

### Step 4: Deploy on Render

1. Go to **render.com** → Sign in with GitHub
2. Click **New** → **Web Service** → Connect your GitHub repo
3. Set environment variables:
   - `SECRET_KEY` = Get from https://djecrety.ir/
   - `ALLOWED_HOSTS` = `teacher-eval-XXXXX.onrender.com` (will show during setup)
   - `USE_S3` = `True` (optional, for file uploads)
   - `EMAIL_HOST_USER` = your Gmail
   - `EMAIL_HOST_PASSWORD` = your Gmail app password

4. Click **Deploy**
5. Wait 5-10 minutes
6. Once deployed, click the URL to test

### Step 5: Create Admin User

In Render dashboard, click your service → **Shell** tab:

```bash
python manage.py createsuperuser
```

### Step 6: (Optional) Add S3 for Unlimited File Storage

If students upload files:

1. **Create S3 bucket**:
   - Go AWS S3 console
   - Create bucket named `teacher-eval-files`
   - Uncheck "Block all public access"

2. **Add AWS credentials to .env:**
   - `AWS_ACCESS_KEY_ID` = (from AWS IAM)
   - `AWS_SECRET_ACCESS_KEY` = (from AWS IAM)
   - `AWS_STORAGE_BUCKET_NAME` = `teacher-eval-files`
   - `USE_S3` = `True`

---

## That's It! ✅

Your app now handles unlimited concurrent students for **FREE**:

- ✅ PostgreSQL database (handles 100+ users simultaneously)
- ✅ Free hosting (sleep mode after 15 min) or $7/month always-on
- ✅ Auto HTTPS/SSL
- ✅ Email notifications (Gmail)
- ✅ File uploads (S3)

---

## Common Issues & Fixes

**"ModuleNotFoundError"** → Add package to `requirements.txt` and redeploy

**"Static files 404"** → WhiteNoise middleware added? Settings.py has `STATIC_ROOT`?

**"Database error"** → Check Render PostgreSQL service is running. Check DATABASE_URL in env vars.

**"502 Bad Gateway"** → Click Render service → **Logs** tab to see error details

---

## Monitor Usage

- **Database**: Render postgresql service dashboard
- **Storage**: AWS S3 console (uploads only)
- **Logs**: Click service → Logs tab
- **Cost**: Usually $0-10/month for 100-1000 students
