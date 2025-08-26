import os, json, warnings
from pathlib import Path
from urllib.parse import urlparse, parse_qs
warnings.filterwarnings("ignore")
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL") 

def build_dsn():
    if DB_URL:
        # psycopg2 accepts libpq URIs directly
        return DB_URL
    # Fallback to discrete env vars (backward compatible)
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "postgres")
    user = os.getenv("DB_USER")
    pwd  = os.getenv("DB_PASS")
    sslm = os.getenv("DB_SSLMODE", "require")
    return f"host={host} port={port} dbname={name} user={user} password={pwd} sslmode={sslm}"

def log_target(dsn: str):
    try:
        u = urlparse(dsn if dsn.startswith("postgres") else
                     f"postgres://{dsn.replace(' ', '').replace('host=', '').replace('port=', ':').replace('dbname=', '/')}")  # best-effort
        host = u.hostname
        port = u.port
        db   = (u.path or "/postgres").lstrip("/") or "postgres"
        qs   = parse_qs(u.query or "")
        sslm = (qs.get("sslmode", ["(none)"])[0])
        print(f"[train] Using host={host} port={port} db={db} sslmode={sslm or '(none)'}")
        if host in (None, "", "localhost", "127.0.0.1"):
            print("[train][WARN] Host looks like localhost — Supabase should be *.supabase.co")
    except Exception:
        print("[train] DSN parsed (hidden for safety).")

import numpy as np
import pandas as pd
import psycopg2
import joblib
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest

def fetch_features(dsn: str) -> pd.DataFrame:
    conn = psycopg2.connect(dsn)
    q = """
      SELECT event_id, hour_of_day, minutes_since_prev, geo_km_from_prev, failed_15m, is_night::int as is_night
      FROM public.login_features
      ORDER BY ts ASC
      LIMIT 20000;
    """
    df = pd.read_sql(q, conn)
    conn.close()
    return df

def main():
    dsn = build_dsn()
    log_target(dsn)

    df = fetch_features(dsn).dropna()
    if df.empty:
        raise SystemExit("No features yet. Insert some login_events and run the Step 3B refresh query first.")

    X = df[["hour_of_day","minutes_since_prev","geo_km_from_prev","failed_15m","is_night"]].values
    scaler = StandardScaler().fit(X)
    Xs = scaler.transform(X)

    iso = IsolationForest(n_estimators=300, contamination=0.03, random_state=42)
    iso.fit(Xs)

    scores = -iso.score_samples(Xs)
    thr = float(np.percentile(scores, 97))  # default threshold @ 97th percentile

    # Save model next to this script so app.py can find it
    out_path = Path(__file__).resolve().parent / "model.pkl"
    joblib.dump({"scaler": scaler, "model": iso, "threshold": thr, "version": "if_v1"}, out_path)
    print(json.dumps({"saved": str(out_path), "threshold": thr, "version": "if_v1"}))

if __name__ == "__main__":
    main()
