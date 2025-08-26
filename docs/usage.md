# Usage Guide

This document explains how to run the project end-to-end, from database setup to automated alerts.

##  Prerequisites
- Python 3.10+
- Supabase project (Postgres)
- n8n cloud or self-hosted
- `uvicorn`, `fastapi`, `scikit-learn`, `joblib`, `psycopg2-binary`

##  Environment
Create `.env` at the repo root (copy `.env.example`):

```ini
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/postgres?sslmode=require
API_PORT=8001
```
## Database Setup

Use Supabase SQL Editor:

If you want a single operation: run sql/setup.sql.

If you prefer split files:

Run sql/schema.sql

Optionally seed a few rows (provided at the bottom of schema.sql/setup.sql)

## Verify:

```sql
SELECT id, user_id, ts, country, city, success
FROM public.login_events
ORDER BY id DESC
LIMIT 5;
```
## Train the Model
```bash
cd fastapi_app
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python train_model.py
```
This creates fastapi_app/model.pkl with a default threshold.


Run the API
```bash
uvicorn fastapi_app.app:app --reload --port 8001
```

Open http://127.0.0.1:8001/docs to test /predict.
```json
Prediction payload example
{
  "items": [
    {
      "event_id": 123,
      "hour_of_day": 2,
      "minutes_since_prev": 9.5,
      "geo_km_from_prev": 800.0,
      "failed_15m": 2,
      "is_night": 1
    }
  ]
}
```
## n8n Workflow

You can either import n8n/login_anomaly_workflow.json or build nodes manually.

**Node Overview**

Set / Build Sample Event
Output a single item with:
```scss
user_id, ts (ISO), ip, country, region, city, lat, lon, device, success
```

A) Insert Event (Postgres → Execute Query)
Use either:

Parameterized SQL + Query Parameters (A–J) to match $1..$11 in queries_for_n8n.sql, or

Expression SQL that embeds JSON safely (if your n8n UI limits parameters).

B) Refresh Features (Postgres)
Execute features_refresh.sql.

C) Select To Score (Postgres)
Select features for the inserted event_id.

D) Score Batch (HTTP)
POST list of feature rows to http://127.0.0.1:8001/predict.

D1) Unwrap Results
Map API response to rows: event_id, model_version, score, threshold, predicted.

E) Upsert Scores (Postgres)
Insert/Update anomaly_scores.

E2) Create Alerts (Postgres)
Insert into security_alerts when score >= threshold.

F) Advance Cursor (optional)
Update meta_run_state.

##  Verify
```sql
SELECT *
FROM public.anomaly_scores
ORDER BY created_at DESC
LIMIT 10;
```
```sql
SELECT *
FROM public.security_alerts
ORDER BY created_at DESC
LIMIT 10;
```
##  Troubleshooting

“null value in column 'user_id'”
The Insert node saw an empty/undefined user_id. Ensure the Set node outputs it and your Insert node reads that item.

“syntax error at or near '{' or '}'”
Too many curly braces in SQL. In n8n, only wrap JavaScript with {{ … }}. Everything else must be plain SQL.

“propertiesString.split is not a function”
The “Query Parameters” field expects a flat array when in “Expression” mode, or comma-separated when in “Fixed”. Don’t pass a raw object.

Timestamps
Use {{$now}} (ISO string) in Set node; cast to ::timestamptz in SQL.

Local API not reachable from n8n Cloud
Use a tunnel (ngrok, Cloudflared) or run n8n locally to access http://127.0.0.1:8001.

## Notes

model.pkl is git-ignored. Generate locally via train_model.py.

Keep secrets in .env, not in code or workflows.
