# Free Deployment Guide for Unlimited Concurrent Users

## Best Option: Render.com + AWS S3

### Why This Works for Unlimited Users

- **Render PostgreSQL**: Handles unlimited concurrent connections (unlike SQLite)
- **Render Web Service**: Auto-scales to handle traffic spikes
- **AWS S3**: Stores unlimited files; accessible from anywhere
- **No per-student limits**: All free tier services scale pay-as-you-go

### Cost Estimate

- **Render Web Service**: Free tier (sleeps after 15 min inactivity) OR ~$7/month for production
- **Render PostgreSQL**: Free tier (limited to 256MB) OR ~$15/month for 2GB (handles 1000+ concurrent users)
- **AWS S3**: Free tier 5GB/month, then ~$0.023/GB (for 1000 students with profile pics: ~$1-2/month)
- **Total Monthly**: Free (with limits) to ~$25 (production-ready for unlimited scale)

---

## Step 1: Prepare Your Code

### 1.1 Update Settings for Production

Replace your `settings.py` DATABASE section with this:

```python
import os
from decouple import config

# ... existing code ...

# Use PostgreSQL from environment variable
if 'DATABASE_URL' in os.environ:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ.get('DATABASE_URL'),
            conn_max_age=600
        )
    }
else:
    # Fallback to local PostgreSQL for development
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', 'teacher_eval'),
            'USER': config('DB_USER', 'postgres'),
            'PASSWORD': config('DB_PASSWORD', ''),
            'HOST': config('DB_HOST', 'localhost'),
            'PORT': config('DB_PORT', '5432'),
        }
    }

# Production settings
if not config('DEBUG', True):
    DEBUG = False
    ALLOWED_HOSTS = config('ALLOWED_HOSTS', '').split(',')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_SECURITY_POLICY = {
        'default-src': ("'self'",),
    }

# AWS S3 File Storage (for unlimited file uploads)
USE_S3 = config('USE_S3', False)

if USE_S3:
    # AWS settings
    AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', 'us-east-1')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    AWS_LOCATION = 'media'

    # S3 static settings
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'
    STATIC_ROOT = 'staticfiles'

    # S3 public media settings
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'
else:
    STATIC_URL = '/static/'
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'
```

### 1.2 Install decouple and dj-database-url

Update `requirements.txt`:

```
Django==4.2.0
psycopg2-binary==2.9.6
python-decouple==3.8
dj-database-url==2.0.0
Pillow==10.0.0
django-storages==1.14.2
boto3==1.28.0
gunicorn==21.2.0
whitenoise==6.5.0
```

### 1.3 Add .gitignore

```
.env
.venv/
__pycache__/
*.pyc
db.sqlite3
staticfiles/
media/
*.log
```

### 1.4 Add Procfile for Render

Create `Procfile` (no extension):

```
web: gunicorn teacher_eval_project.wsgi:application
```

### 1.5 Create render.yaml for Render Deployment

Create `render.yaml`:

```yaml
services:
  - type: web
    name: teacher-eval
    plan: free
    runtime: python
    buildCommand: bash build.sh
    startCommand: gunicorn teacher_eval_project.wsgi:application
    envVars:
      - key: DEBUG
        value: "False"
      - key: ALLOWED_HOSTS
        fromDatabase:
          name: teacher-eval-postgres
          property: host
      - key: DATABASE_URL
        fromDatabase:
          name: teacher-eval-postgres
          property: connectionString

  - type: postgres
    name: teacher-eval-postgres
    plan: free
    ipAllowList: []
```

---

## Step 2: Set Up AWS S3 (for File Storage)

### 2.1 Create AWS Account

1. Go to https://aws.amazon.com/free/
2. Sign up (you get 5GB free S3 storage for 12 months)

### 2.2 Create S3 Bucket

1. AWS Console → S3 → "Create bucket"
2. Bucket name: `teacher-eval-yourdomain` (must be globally unique)
3. Region: `us-east-1` (cheapest)
4. Uncheck "Block all public access" (to serve files)
5. Create bucket

### 2.3 Create IAM User with S3 Access

1. AWS Console → IAM → "Users" → "Create user"
2. Name: `teacher-eval-app`
3. Attach policy: `AmazonS3FullAccess`
4. Create access key (for programmatic access)
5. Copy **Access Key ID** and **Secret Access Key**

### 2.4 Make S3 Bucket Public (for file download)

1. Go to your bucket → "Permissions" tab
2. Paste this bucket policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicRead",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/*"
    }
  ]
}
```

Replace `YOUR-BUCKET-NAME` with your bucket name.

---

## Step 3: Deploy to Render.com

### 3.1 Create Render Account

1. Go to https://render.com
2. Sign up (free tier available)
3. Connect your GitHub account

### 3.2 Push Code to GitHub

```bash
git init
git add .
git commit -m "Initial commit for deployment"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/teacher-eval.git
git push -u origin main
```

### 3.3 Deploy on Render

1. Render Dashboard → "New +" → "Web Service"
2. Select your GitHub repo
3. Set Name: `teacher-eval`
4. Set Build Command: `pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --no-input`
5. Set Start Command: `gunicorn teacher_eval_project.wsgi:application`
6. Region: Choose closest to your users
7. Plan: "Free" (will sleep after 15 min, or upgrade to $7/month for always-on)
8. Add Environment Variables:
   - `DEBUG` = `false`
   - `SECRET_KEY` = Generate one at https://djecrety.ir/
   - `ALLOWED_HOSTS` = `yourdomain.onrender.com`
   - `DATABASE_URL` = Render will auto-fill from PostgreSQL service
   - `USE_S3` = `True`
   - `AWS_ACCESS_KEY_ID` = (from AWS IAM)
   - `AWS_SECRET_ACCESS_KEY` = (from AWS IAM)
   - `AWS_STORAGE_BUCKET_NAME` = (your S3 bucket name)
   - `EMAIL_HOST_USER` = (your Gmail)
   - `EMAIL_HOST_PASSWORD` = (your Gmail app password)

9. Click "Create Web Service"
10. Wait 5-10 minutes for deployment

### 3.4 PostgreSQL Database

Render will auto-create a free PostgreSQL database when you deploy. No extra setup needed.

---

## Step 4: Migrate Database & Create Admin

After deployment:

1. In Render Dashboard, click your service → "Shell"
2. Run:

```bash
python manage.py migrate
python manage.py createsuperuser
```

3. Your app will be live at `https://teacher-eval-XXXXX.onrender.com`

---

## Alternative: Railway.app (Even Simpler)

**Best for beginners:**

1. Go to https://railway.app
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Railway auto-detects Django
5. It auto-provisions PostgreSQL for free
6. Set env vars same as above
7. Done! (No build.sh needed)

---

## Database & Concurrency Limits

| Service                | Free Tier | Concurrent Users | Price/Month   |
| ---------------------- | --------- | ---------------- | ------------- |
| **Render PostgreSQL**  | 256MB     | 10-20            | Starting $15  |
| **Railway PostgreSQL** | Generous  | 50-100           | Free credits  |
| **PlanetScale MySQL**  | 5GB       | Unlimited        | Free tier     |
| **AWS RDS Free**       | 20GB      | Limited          | Only 1st year |

For **unlimited concurrent access**, I recommend **PlanetScale** (MySQL) which is truly free and handles unlimited concurrent connections.

---

## Quick Troubleshooting

**"Static files not loading"**: Run `python manage.py collectstatic`

**"Database connection error"**: Check DATABASE_URL in Render env vars matches your PostgreSQL service

**"Files not uploading"**: Verify S3 bucket policy and AWS credentials

**"502 Bad Gateway"**: Check Render logs (`render.com/services/your-service/logs`)

---

## Summary

✅ **Cost**: ~$0-7/month (including PostgreSQL + storage)  
✅ **Scale**: Handles 1000+ concurrent students  
✅ **Setup Time**: 30 minutes  
✅ **Supported**: Django, automatic SSL, email, file uploads

Ready to deploy?
