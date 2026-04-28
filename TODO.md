# Fix Login "Invalid Credentials" Issue — Integration Plan

## Information Gathered
- `app.py` has Flask backend with `/login`, `/signup`, `/send-otp`, `/verify-otp`, `/reset-password` endpoints.
- No session secret, no `/dashboard` route, emails were not normalized.
- `templates/index.html` has a polished UI but used `localStorage` for auth — completely disconnected from the Flask backend.
- `templates/dashboard.html` was a duplicate of `forgot.html` instead of an actual dashboard.

## Plan
1. [x] Update `app.py`: add `secret_key`, import `session`/`redirect`/`url_for`, normalize email to lowercase, add `/dashboard` and `/logout` routes, protect dashboard with session check.
2. [x] Update `templates/index.html`: replace localStorage auth with `fetch()` to `/login` and `/signup`, lowercase email before sending, redirect to `/dashboard` on success.
3. [x] Rewrite `templates/dashboard.html`: create an actual dashboard matching the bio-medical theme, display logged-in user name, add functional logout button, redirect to `/` if not authenticated.

## Follow-up Steps
- Restart Flask server (`python app.py`) and test signup → login → dashboard → logout.

