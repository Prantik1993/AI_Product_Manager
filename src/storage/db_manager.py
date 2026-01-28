import sqlite3
import json
import os
from datetime import datetime
from src.config.settings import settings
from src.monitoring.logger import get_logger

logger = get_logger("db_manager")

def init_db():
    """Initialize the SQLite database schema."""
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(settings.DB_PATH), exist_ok=True)
        
        conn = sqlite3.connect(settings.DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_input TEXT,
                timestamp DATETIME,
                decision TEXT,
                full_report JSON
            )
        ''')
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {settings.DB_PATH}")
    except Exception as e:
        logger.error(f"Failed to initialize DB: {e}")

def save_analysis(user_input: str, decision: str, full_state: dict):
    """Save a completed analysis to the database."""
    try:
        conn = sqlite3.connect(settings.DB_PATH)
        cursor = conn.cursor()
        
        # Serialize the state dictionary to JSON
        report_json = json.dumps(full_state, default=str)
        
        cursor.execute('''
            INSERT INTO reports (user_input, timestamp, decision, full_report)
            VALUES (?, ?, ?, ?)
        ''', (user_input, datetime.now(), decision, report_json))
        
        conn.commit()
        conn.close()
        logger.info(f"Report saved for: {user_input[:30]}...")
    except Exception as e:
        logger.error(f"Failed to save report: {e}")

def get_history():
    """Fetch all past reports, newest first."""
    if not os.path.exists(settings.DB_PATH):
        return []
        
    try:
        conn = sqlite3.connect(settings.DB_PATH)
        conn.row_factory = sqlite3.Row  # Allows accessing columns by name
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM reports ORDER BY timestamp DESC')
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        logger.error(f"Failed to fetch history: {e}")
        return []