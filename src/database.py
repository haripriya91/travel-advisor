import sqlite3
from pathlib import Path
  
# Locate the project root regardless of the terminal's working directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
  
DATABASE_PATH = PROJECT_ROOT / "traveladvisor.db"
  
  
def get_connection():
    """Open a connection to the SQLite database."""
    connection = sqlite3.connect(DATABASE_PATH, timeout=10)
  
    # Return each row as a dictionary-like sqlite3.Row object.
    connection.row_factory = sqlite3.Row
  
    # Enable foreign-key enforcement for this connection.
    connection.execute("PRAGMA foreign_keys = ON")
  
    return connection
  
  
def create_tables():
    """Create the required tables if they do not already exist."""
  
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                  id TEXT PRIMARY KEY,
                  title TEXT NOT NULL DEFAULT 'New Travel Plan',
                  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
  
            CREATE TABLE IF NOT EXISTS messages (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  conversation_id TEXT NOT NULL,
                  role TEXT NOT NULL
                      CHECK (role IN ('user', 'assistant')),
                  content TEXT NOT NULL,
                  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (conversation_id)
                      REFERENCES conversations(id)
                      ON DELETE CASCADE
            );
  
            CREATE TABLE IF NOT EXISTS trips (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  conversation_id TEXT NOT NULL UNIQUE,
                  trip_state_json TEXT NOT NULL DEFAULT '{}',
                  itinerary_json TEXT,
                  status TEXT NOT NULL DEFAULT 'collecting',
                  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (conversation_id)
                      REFERENCES conversations(id)
                      ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS api_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT NOT NULL,
                model TEXT NOT NULL,
                input_tokens INTEGER NOT NULL DEFAULT 0,
                output_tokens INTEGER NOT NULL DEFAULT 0,
                cached_tokens INTEGER NOT NULL DEFAULT 0,
                total_tokens INTEGER NOT NULL DEFAULT 0,
                estimated_cost_usd REAL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
  
  
if __name__ == "__main__":
    create_tables()
    print(f"Database ready: {DATABASE_PATH}")