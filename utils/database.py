"""
SQLite database utilities for persisting investment team profiles.
"""

import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "profiles.db")


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS research_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_url TEXT NOT NULL,
            created_at TEXT NOT NULL,
            people_found INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            name TEXT NOT NULL,
            title TEXT,
            organization TEXT,
            source_url TEXT,
            baseline_bio TEXT,
            ai_profile TEXT,
            linkedin_url TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES research_sessions(id)
        )
    """)
    conn.commit()
    conn.close()


def save_session(source_url: str, people_count: int) -> int:
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO research_sessions (source_url, created_at, people_found) VALUES (?, ?, ?)",
        (source_url, datetime.now().isoformat(), people_count)
    )
    session_id = cur.lastrowid
    conn.commit()
    conn.close()
    return session_id


def save_profile(session_id: int, profile: dict):
    conn = get_connection()
    conn.execute("""
        INSERT INTO profiles 
        (session_id, name, title, organization, source_url, baseline_bio, ai_profile, linkedin_url, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session_id,
        profile.get("name", ""),
        profile.get("title", ""),
        profile.get("organization", ""),
        profile.get("source_url", ""),
        profile.get("baseline_bio", ""),
        profile.get("ai_profile", ""),
        profile.get("linkedin_url", ""),
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()


def get_recent_sessions(limit: int = 10) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM research_sessions ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_profiles_for_session(session_id: int) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM profiles WHERE session_id = ? ORDER BY name", (session_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_profiles() -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT p.*, s.source_url as session_url FROM profiles p JOIN research_sessions s ON p.session_id = s.id ORDER BY p.created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
