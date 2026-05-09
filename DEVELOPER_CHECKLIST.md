# ✅ Developer Checklist - Security Setup

## Phase 1: Initial Setup (Do This First)

### Installation
- [ ] Run `pip install -r requirements.txt`
- [ ] Verify `python-dotenv` is installed: `pip list | grep python-dotenv`

### Environment File
- [ ] Copy `.env.example` to `.env`: `cp .env.example .env`
- [ ] Verify `.env` file exists in project root
- [ ] Verify `.env` is in `.gitignore`

### Credentials
- [ ] Get Google Client ID from Google Cloud Console
- [ ] Get Google Client Secret from Google Cloud Console
- [ ] Get Gmail app password (not main password)
- [ ] Edit `.env` and fill in all credentials:
  ```env
  GOOGLE_CLIENT_ID=your-client-id
  GOOGLE_CLIENT_SECRET=your-client-secret
  EMAIL_HOST_USER=your-email@gmail.com
  EMAIL_HOST_PASSWORD=your-app-password
  ```

### Verification
- [ ] Run `python manage.py setup_google_oauth`
- [ ] Check output shows "✓ Google OAuth setup complete!"
- [ ] Run `python manage.py runserver`
- [ ] Verify no errors in console
- [ ] Test login with Google OAuth

---

## Phase 2: Git Setup (Before First Commit)

### Git Configuration
- [ ] Verify `.gitignore` contains `.env`
- [ ] Run `git status` and verify `.env` is NOT listed
- [ ] Run `git status` and verify `.env.example` IS listed
- [ ] Verify no credentials appear in `git diff`

### Commit
- [ ] Stage files: `git add .`
- [ ] Review changes: `git diff --cached`
- [ ] Verify NO credentials in diff
- [ ] Commit: `git commit -m "Add environment variable security"`
- [ ] Push: `git push`

### Verification
- [ ] Check GitHub/GitLab - verify `.env` is NOT there
- [ ] Check GitHub/GitLab - verify `.env.example` IS there
- [ ] Verify no credentials in commit history

---

## Phase 3: Team Setup (For Other Developers)

### Documentation
- [ ] Share `QUICK_SETUP.md` with team
- [ ] Share `ENV_SETUP_GUIDE.md` with team
- [ ] Explain `.env` is NOT in git (it's in `.gitignore`)

### Credentials Distribution
- [ ] Create secure method to share credentials (NOT email/chat)
- [ ] Use password manager or secure sharing tool
- [ ] Each developer creates their own `.env` file
- [ ] Each developer fills in credentials locally

### Verification
- [ ] Each developer runs `python manage.py setup_google_oauth`
- [ ] Each developer tests with `python manage.py runserver`
- [ ] Verify no `.env` files are committed

---

## Phase 4: Production Setup (Before Deployment)

### Environment Variables
- [ ] Generate new `SECRET_KEY` for production
- [ ] Set `DEBUG=False` for production
- [ ] Update `ALLOWED_HOSTS` with production domain
- [ ] Get production Google OAuth credentials
- [ ] Get production email credentials

### Hosting Platform Setup
- [ ] Log into hosting platform (Heroku/AWS/DigitalOcean/etc)
- [ ] Set environment variables:
  ```bash
  SECRET_KEY=your-production-secret-key
  DEBUG=False
  ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
  GOOGLE_CLIENT_ID=production-client-id
  GOOGLE_CLIENT_SECRET=production-client-secret
  EMAIL_HOST_USER=production-email@gmail.com
  EMAIL_HOST_PASSWORD=production-app-password
  SESSION_COOKIE_SECURE=True
  ```

### Security Verification
- [ ] Verify `DEBUG=False` in production
- [ ] Verify `SESSION_COOKIE_SECURE=True` in production
- [ ] Verify HTTPS is enabled
- [ ] Verify credentials are different from development
- [ ] Verify `.env` file is NOT deployed

### Testing
- [ ] Test login with Google OAuth in production
- [ ] Test email sending in production
- [ ] Verify no errors in production logs
- [ ] Verify no credentials in logs

---

## Phase 5: Ongoing Maintenance

### Regular Tasks
- [ ] Review `.gitignore` monthly
- [ ] Rotate credentials every 3-6 months
- [ ] Update `requirements.txt` when needed
- [ ] Review security documentation

### Credential Rotation
- [ ] Generate new Google OAuth credentials
- [ ] Generate new email app password
- [ ] Update `.env` locally
- [ ] Update production environment variables
- [ ] Test everything works
- [ ] Delete old credentials

### Team Updates
- [ ] When new developer joins:
  - [ ] Share `QUICK_SETUP.md`
  - [ ] Share credentials securely
  - [ ] Verify they set up `.env` correctly
  - [ ] Verify they don't commit `.env`

---

## 🔍 Security Audit Checklist

### Code Review
- [ ] No hardcoded credentials in code
- [ ] All sensitive settings use `os.getenv()`
- [ ] `.env` is in `.gitignore`
- [ ] `.env.example` is in git (without real values)
- [ ] No credentials in comments

### Git History
- [ ] Run `git log -p | grep -i password` - should return nothing
- [ ] Run `git log -p | grep -i secret` - should return nothing
- [ ] Run `git log -p | grep -i token` - should return nothing
- [ ] Run `git log -p | grep -i key` - should return nothing

### File System
- [ ] `.env` file exists locally
- [ ] `.env` file is NOT in git
- [ ] `.env.example` file IS in git
- [ ] `.gitignore` contains `.env`
- [ ] No backup `.env` files lying around

### Environment Variables
- [ ] All required variables are set
- [ ] No placeholder values in production
- [ ] Production credentials are different from development
- [ ] Credentials are strong and unique

---

## 📋 Troubleshooting Checklist

### If Setup Fails
- [ ] Verify `.env` file exists: `ls -la .env`
- [ ] Verify `.env` has correct format: `cat .env`
- [ ] Verify `python-dotenv` is installed: `pip list | grep python-dotenv`
- [ ] Verify credentials are correct in `.env`
- [ ] Run `python manage.py setup_google_oauth` again
- [ ] Check error messages carefully

### If OAuth Doesn't Work
- [ ] Verify `GOOGLE_CLIENT_ID` in `.env`
- [ ] Verify `GOOGLE_CLIENT_SECRET` in `.env`
- [ ] Verify redirect URIs in Google Cloud Console
- [ ] Run `python manage.py setup_google_oauth` again
- [ ] Restart development server

### If Email Doesn't Work
- [ ] Verify `EMAIL_HOST_USER` in `.env`
- [ ] Verify `EMAIL_HOST_PASSWORD` is app password (not main password)
- [ ] Verify Gmail 2FA is enabled
- [ ] Verify app password is correct
- [ ] Check firewall allows SMTP port 465

### If Credentials Leak
- [ ] IMMEDIATELY revoke leaked credentials
- [ ] Generate new credentials
- [ ] Update `.env` locally
- [ ] Update production environment variables
- [ ] Notify team members
- [ ] Review git history for exposure

---

## 📞 Quick Reference

### Common Commands
```bash
# Setup
pip install -r requirements.txt
cp .env.example .env
python manage.py setup_google_oauth

# Development
python manage.py runserver

# Git
git status
git diff
git log -p

# Verification
python manage.py shell
>>> import os
>>> os.getenv('GOOGLE_CLIENT_ID')
```

### File Locations
- `.env` - Local credentials (NOT in git)
- `.env.example` - Template (in git)
- `.gitignore` - Excludes `.env`
- `myproject/settings.py` - Uses `os.getenv()`
- `requirements.txt` - Dependencies

### Documentation
- `QUICK_SETUP.md` - Quick reference
- `ENV_SETUP_GUIDE.md` - Comprehensive guide
- `SECURITY_IMPLEMENTATION.md` - Security summary
- `BEFORE_AFTER_COMPARISON.md` - Before/after

---

## ✅ Final Verification

Before considering setup complete:

- [ ] `.env` file created and filled with credentials
- [ ] `python-dotenv` installed
- [ ] `setup_google_oauth` command executed successfully
- [ ] Development server runs without errors
- [ ] Google OAuth login works
- [ ] Email sending works
- [ ] `.env` is in `.gitignore`
- [ ] `.env` is NOT committed to git
- [ ] All documentation reviewed
- [ ] Team members notified

---

## 🎉 Setup Complete!

When all checkboxes are checked, your security setup is complete and production-ready.

**Remember**: Never commit `.env` file. Always use `.env.example` as template.

For questions, refer to the documentation files or contact your team lead.
