"""
Database helper module for Tour de France Analytics System.
Connects to SQLite database `tdf.db` and provides clean query execution.
"""

import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path(__file__).parent / "tdf.db"

def get_connection():
    """Returns a connection to the SQLite database with row factory."""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def execute_query(query: str, params: tuple = ()) -> pd.DataFrame:
    """Executes a SQL query and returns a pandas DataFrame."""
    conn = get_connection()
    try:
        df = pd.read_sql_query(query, conn, params=params)
        return df
    finally:
        conn.close()

def format_seconds(seconds: float or int) -> str:
    """Formats seconds into hh:mm:ss format."""
    if pd.isna(seconds) or seconds is None:
        return "-"
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}h {m:02d}m {s:02d}s"

def format_gap(gap_seconds: float or int) -> str:
    """Formats time gap in seconds into '+ hh:mm:ss' format."""
    if pd.isna(gap_seconds) or gap_seconds is None or gap_seconds == 0:
        return "-"
    gap_seconds = int(gap_seconds)
    sign = "+" if gap_seconds >= 0 else "-"
    gap_seconds = abs(gap_seconds)
    h = gap_seconds // 3600
    m = (gap_seconds % 3600) // 60
    s = gap_seconds % 60
    if h > 0:
        return f"{sign}{h:02d}h {m:02d}m {s:02d}s"
    elif m > 0:
        return f"{sign}{m:02d}m {s:02d}s"
    else:
        return f"{sign}{s:02d}s"
