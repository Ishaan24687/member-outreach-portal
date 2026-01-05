# Member Outreach Portal

I built this as a personal version of the outreach platform I worked on at Lantern. Coordinators needed a way to see which patients were likely to miss their appointments so they could do proactive outreach. At Lantern we were handling 2K+ appointments monthly, and the biggest pain point was figuring out *who* to call — coordinators were spending hours manually reviewing schedules instead of actually reaching out to members.

This system combines a Django web app with an integrated ML model that predicts patient no-shows. Coordinators log in, see a ranked list of high-risk appointments, and can track their outreach efforts all in one place. The model I trained on our synthetic dataset gets about 0.81 AUC, which lines up with what we saw in production — the real win was that proactive outreach improved show-up rates by 28%.

## Features

- **No-Show Prediction Model** — GradientBoosting classifier that scores upcoming appointments by no-show risk. Uses features like historical no-show rate, days until appointment, appointment type, day of week, and past outreach history.
- **Coordinator Dashboard** — KPI cards showing total members, monthly appointments, current no-show rate, and outreach conversion rate. Trend charts for week-over-week tracking.
- **Member Profiles** — Full view of each member's appointment history, outreach log, and current risk score. One-click prediction for any upcoming appointment.
- **Outreach Tracking** — Log phone calls, SMS, and emails. Track outcomes (reached, voicemail, no answer) so we can measure what actually works.
- **Analytics API** — Endpoints for outreach effectiveness by channel, coordinator performance metrics, and weekly trend data.
- **REST API** — Full DRF-powered API for all resources. Built so a React or Streamlit frontend could plug in easily.

## Tech Stack

- **Backend**: Django 5.0, Django REST Framework
- **ML**: scikit-learn (GradientBoostingClassifier), pandas, numpy
- **Database**: PostgreSQL
- **Frontend**: Django templates, Bootstrap 5, Chart.js
- **Infrastructure**: Docker, docker-compose, Gunicorn, WhiteNoise

## How to Run

```bash
# clone the repo
git clone https://github.com/ishaangupta/member-outreach-portal.git
cd member-outreach-portal

# copy env file
cp .env.example .env

# train the model (generates synthetic data + trains classifier)
pip install -r requirements.txt
python ml/train.py

# start everything
docker-compose up --build

# in another terminal, run migrations and seed data
docker-compose exec web python manage.py migrate
docker-compose exec web python seed_data.py
```

The app will be at http://localhost:8000

## Model Performance

Trained on 5,000 synthetic appointment records with realistic correlations:

| Metric    | Score |
|-----------|-------|
| AUC-ROC   | 0.81  |
| Precision | 0.74  |
| Recall    | 0.68  |
| F1        | 0.71  |

Top features by importance:
1. Historical no-show rate (0.31)
2. Days until appointment (0.18)
3. Past outreach count (0.12)
4. Appointment type (0.11)
5. Day of week (0.09)

## Screenshots

*Dashboard view:*
![Dashboard](docs/screenshots/dashboard.png)

*Member detail with risk prediction:*
![Member Detail](docs/screenshots/member_detail.png)

*High-risk appointments list:*
![High Risk](docs/screenshots/high_risk.png)

## API Endpoints

| Method | Endpoint                          | Description                        |
|--------|-----------------------------------|------------------------------------|
| GET    | /api/members/                     | List all members (searchable)      |
| GET    | /api/members/{id}/                | Member detail                      |
| GET    | /api/members/{id}/risk_score/     | Get ML risk prediction for member  |
| GET    | /api/appointments/                | List appointments                  |
| POST   | /api/appointments/                | Create appointment                 |
| POST   | /api/predictions/predict/{id}/    | Predict no-show for appointment    |
| GET    | /api/predictions/high-risk/       | All high-risk upcoming appointments|
| GET    | /api/analytics/overview/          | Dashboard KPIs                     |
| GET    | /api/analytics/trends/            | Weekly no-show trends              |
| GET    | /api/analytics/outreach-effectiveness/ | Outreach channel comparison   |
| GET    | /api/analytics/coordinator-performance/ | Coordinator metrics          |

## What I'd Do Next

- Integrate with a real scheduling API (Epic FHIR, Athena, etc.)
- Add authentication and role-based access for coordinators vs supervisors
- Build a Streamlit dashboard for quick ad-hoc analysis (I had one at Lantern)
- Set up Airflow DAGs to retrain the model weekly on new appointment outcomes
- Add SMS/email integration so outreach can be triggered directly from the portal
