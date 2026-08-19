import sqlite3

DB_NAME = "pipeline_history.db"


def init_db():
    """Database aur table banao (agar already nahi hai to)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            branch TEXT,
            commit_message TEXT,
            commit_sha TEXT,
            status TEXT,
            root_cause TEXT,
            explanation TEXT,
            suggested_fix TEXT,
            severity TEXT,
            auto_fixable BOOLEAN,
            self_heal_action TEXT,
            created_at TEXT,
            logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print(f"✅ Database '{DB_NAME}' ready hai, table 'pipeline_runs' ban gaya.")


if __name__ == "__main__":
    init_db()