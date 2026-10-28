from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def now():
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = root / "geoalibi.sqlite3"
        with self.connect() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, created TEXT, title TEXT, report TEXT);
            CREATE TABLE IF NOT EXISTS reviews(id INTEGER PRIMARY KEY, run_id TEXT, region_id TEXT, decision TEXT, note TEXT, created TEXT);
            CREATE TABLE IF NOT EXISTS evidence(id INTEGER PRIMARY KEY, run_id TEXT, region_id TEXT, request_index INTEGER, status TEXT, source TEXT, note TEXT, created TEXT);
            CREATE TABLE IF NOT EXISTS reservations(id INTEGER PRIMARY KEY, dollars REAL, created TEXT);
            CREATE TABLE IF NOT EXISTS cache(key TEXT PRIMARY KEY, value TEXT);
            """)

    def connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        return db

    def save(self, run_id, title, report):
        with self.connect() as db:
            db.execute("INSERT INTO runs VALUES(?,?,?,?)", (run_id, now(), title, json.dumps(report)))

    def get(self, run_id):
        with self.connect() as db:
            row = db.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
            if not row:
                return None
            report = json.loads(row["report"])
            report["created"] = row["created"]
            report["title"] = row["title"]
            reviews = db.execute("SELECT region_id, decision, note, created FROM reviews WHERE run_id=? ORDER BY id", (run_id,)).fetchall()
            report["evidence_audit"] = [dict(row) for row in db.execute("SELECT region_id,request_index,status,source,note,created FROM evidence WHERE run_id=? ORDER BY id", (run_id,))]
            report["audit"] = [dict(r) for r in reviews]
            for item in reviews:
                for region in report["regions"]:
                    if region["id"] == item["region_id"]:
                        region["review"] = item["decision"]
                        region["review_note"] = item["note"]
            return report

    def recent(self):
        with self.connect() as db:
            return [dict(row) for row in db.execute("SELECT id,created,title FROM runs ORDER BY created DESC LIMIT 30")]

    def review(self, run_id, region_id, decision, note):
        with self.connect() as db:
            db.execute("INSERT INTO reviews(run_id,region_id,decision,note,created) VALUES(?,?,?,?,?)", (run_id, region_id, decision, note, now()))

    def add_evidence(self, run_id, region_id, request_index, status, source, note):
        with self.connect() as db:
            db.execute("INSERT INTO evidence(run_id,region_id,request_index,status,source,note,created) VALUES(?,?,?,?,?,?,?)",
                       (run_id, region_id, request_index, status, source, note, now()))

    def reserve(self, dollars, ceiling):
        # A conservative, persistent per-request reservation. Retained even on failure:
        # the provider may have processed a request despite a client-side timeout.
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            used = db.execute("SELECT COALESCE(SUM(dollars),0) FROM reservations").fetchone()[0]
            if used + dollars > ceiling:
                raise ValueError("Local API reservation ceiling reached. Increase GEOALIBI_API_BUDGET_USD only after checking Meta Billing.")
            db.execute("INSERT INTO reservations(dollars,created) VALUES(?,?)", (dollars, now()))

    def budget(self, ceiling):
        with self.connect() as db:
            used = db.execute("SELECT COALESCE(SUM(dollars),0) FROM reservations").fetchone()[0]
        return {"reserved_usd": round(used, 4), "ceiling_usd": ceiling, "note": "Conservative local reservations; not actual charges or a Meta account spending cap."}

    def cached(self, key):
        with self.connect() as db:
            row = db.execute("SELECT value FROM cache WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def cache(self, key, value):
        with self.connect() as db:
            db.execute("INSERT OR REPLACE INTO cache VALUES(?,?)", (key, json.dumps(value)))


