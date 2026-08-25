# SkillSwap — Peer-to-Peer Student Skill Exchange (Hackathon MVP)

Teach what you know → Earn SkillCoins → Spend SkillCoins → Learn a new skill.

## Run it

```bash
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000** in your browser. The database (SQLite) and demo
data are created automatically the first time you run the app.

If you ever want to reset the demo data, visit `/seed-demo` (or click
"Reset / Seed Demo Data" on the landing page).

## Demo login

Fastest option for judges: click **"Quick login as Rahul"** or **"Quick login
as Kabir"** on the landing/login page — no typing needed.

| Email | Password |
|---|---|
| rahul@skillswap.dev | password123 |
| aman@skillswap.dev | password123 |
| priya@skillswap.dev | password123 |
| arjun@skillswap.dev | password123 |
| sneha@skillswap.dev | password123 |
| kabir@skillswap.dev | password123 |

Kabir's account comes pre-loaded with a pending session request and an
accepted session with an existing chat thread + meeting link, so the chat/
notifications features are visible immediately without setup.

## 3-minute demo script

1. Log in as **Rahul** (teaches Python/C++, wants Video Editing).
2. Open **AI Matches** → Aman shows up as a top match with a match %
   and "Why this match?" explanation.
3. Open **Aman's profile** → **Request Session** for Video Editing.
4. Log out, log in as **Aman** → **Sessions** → **Accept**, then
   **Mark Completed**.
5. Log in as **Kabir** to show the notification bell, chat thread, and
   meeting link already populated.
5. SkillCoins transfer automatically (Rahul −25, Aman +25) — visible
   immediately in both **Wallets**.
6. Log back in as **Rahul** → **Sessions** → **Rate Session** → Aman's
   rating updates on his profile.

## How the AI matching works

No external ML service is required (per the hackathon brief, the app must
work even without one). `matching.py` implements a lightweight
keyword/category similarity fallback:

- **Skill similarity (60%)** — exact skill match scores 1.0; a
  related skill (e.g. wanting "Data Analysis" matches a teacher
  offering "Python"/"Excel") scores 0.7; same category scores 0.4.
- **Skill level (15%)** — based on the teacher's proficiency level.
- **Teacher rating (15%)** — average rating from past sessions.
- **Mutual exchange (10%)** — bonus if the teacher also wants a skill
  the student can teach.

Every match shows the reasons behind its score for the demo/pitch.

## Project structure

```
skillswap/
├── app.py            # Flask routes & business logic
├── config.py         # App configuration
├── models.py         # SQLAlchemy models
├── matching.py        # AI-style matching engine
├── seed.py            # Demo data seeding
├── requirements.txt
├── templates/          # Jinja2 templates (Bootstrap 5 UI)
└── static/
    ├── css/style.css
    └── js/app.js
```

## What's intentionally out of scope (per hackathon brief)

Chat, video calling, payments, mobile app, email verification, OAuth,
real-time notifications, AI chatbot, resume parser, and microservices
were deliberately left out to keep this a reliable, demo-ready MVP.
