# Quick Setup Reference

## 🚀 Quick Start (5 minutes)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy example env file
cp .env.example .env

# 3. Edit .env with your credentials
# Open .env and fill in:
#   - GOOGLE_CLIENT_ID
#   - GOOGLE_CLIENT_SECRET
#   - EMAIL_HOST_USER
#   - EMAIL_HOST_PASSWORD

# 4. Run setup command
python manage.py setup_google_oauth

# 5. Start development server
python manage.py runserver
```

## 📋 Required Environment Variables

| Variable | Example | Notes |
|----------|---------|-------|
| `GOOGLE_CLIENT_ID` | `860984795493-...` | From Google Cloud Console |
| `GOOGLE_CLIENT_SECRET` | `GOCSPX-...` | From Google Cloud Console |
| `EMAIL_HOST_USER` | `your-email@gmail.com` | Gmail address |
| `EMAIL_HOST_PASSWORD` | `app-password` | Gmail app password (not main password) |
| `SECRET_KEY` | `django-insecure-...` | Django secret key |
| `DEBUG` | `True` | Set to `False` in production |

## 🔒 Security Checklist

- [ ] `.env` file created and added to `.gitignore`
- [ ] All credentials filled in `.env`
- [ ] `python-dotenv` installed (`pip install python-dotenv`)
- [ ] `setup_google_oauth` command executed successfully
- [ ] `.env` file is NOT committed to git
- [ ] Production credentials are different from development

## 🐛 Common Issues

| Issue | Solution |
|-------|----------|
| "GOOGLE_CLIENT_ID not found" | Check `.env` file exists in project root |
| Email not sending | Use Gmail app password, not main password |
| Settings not loading | Run `pip install python-dotenv` |
| OAuth not working | Run `python manage.py setup_google_oauth` |

## 📁 File Structure

```
chhapadiya/
├── .env                          # ← Your credentials (NOT in git)
├── .env.example                  # ← Template (in git)
├── .gitignore                    # ← Excludes .env
├── requirements.txt              # ← Dependencies
├── ENV_SETUP_GUIDE.md           # ← Full guide
├── myproject/
│   └── settings.py              # ← Uses os.getenv()
└── web/
    └── management/commands/
        └── setup_google_oauth.py # ← Uses environment variables
```

## 🔑 Getting Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Google+ API
4. Create OAuth 2.0 credentials (Web application)
5. Add authorized redirect URIs:
   - `http://localhost:8000/accounts/google/login/callback/`
   - `http://localhost:8000/accounts/google/login/callback`
6. Copy Client ID and Client Secret to `.env`

## 📧 Getting Gmail App Password

1. Enable 2-Factor Authentication on your Google account
2. Go to [App Passwords](https://myaccount.google.com/apppasswords)
3. Select "Mail" and "Windows Computer" (or your device)
4. Copy the generated 16-character password
5. Paste into `.env` as `EMAIL_HOST_PASSWORD`

## ✅ Verify Setup

```bash
python manage.py shell
>>> from django.conf import settings
>>> settings.DEBUG
True
>>> settings.EMAIL_HOST_USER
'your-email@gmail.com'
```

## 🚀 Ready to Deploy?

Before pushing to production:
1. Generate new `SECRET_KEY`
2. Set `DEBUG=False`
3. Update `ALLOWED_HOSTS` with your domain
4. Set environment variables on your hosting platform
5. Never commit `.env` file
