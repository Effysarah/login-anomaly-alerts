Login Anomaly Detection & Automated Alerting

Detect and respond to suspicious login activity using Supabase (Postgres), FastAPI (Python), and n8n automation.
This project demonstrates how to combine machine learning anomaly detection with workflow automation to raise real-time security alerts.

🚀 Features

Event ingestion → Store raw login events in Postgres via n8n.

Feature engineering → Derive login features (hour of day, geo distance, failed attempts, etc.).

ML scoring → IsolationForest model served via FastAPI.

Alerting pipeline → Automatic anomaly scores + alert creation when thresholds are crossed.

Modular design → SQL schema, Python API, and n8n workflow are loosely coupled.

📂 Project Structure
.
├─ fastapi_app/         # Model training & scoring API
├─ sql/                 # Database schema & helper queries
├─ docs/                # Usage and workflow documentation
├─ n8n/                 # (optional) exported workflow JSON
└─ README.md

🛠️ Quick Start

Set up database schema (Supabase SQL editor):
Run sql/setup.sql or see docs/usage.md for split files.

Train the model:

cd fastapi_app
pip install -r requirements.txt
python train_model.py


Run the API:

uvicorn fastapi_app.app:app --reload --port 8001


Orchestrate with n8n:
Import or rebuild workflow nodes using the queries in sql/queries_for_n8n.sql.

📖 Documentation

For detailed setup, workflows, and troubleshooting, see:
👉 docs/usage.md

📸 Demo Queries

Recent events:

SELECT id, user_id, ts, country, city, success
FROM public.login_events
ORDER BY id DESC
LIMIT 5;


Alerts:

SELECT created_at, event_id, severity, message
FROM public.security_alerts
ORDER BY created_at DESC
LIMIT 10;

📜 License

MIT (or your choice)

✨ This repo shows how to blend AI/ML anomaly detection with workflow automation to protect authentication systems in real time.