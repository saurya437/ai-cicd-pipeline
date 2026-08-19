import sqlite3

DB_NAME = "pipeline_history.db"


def log_run(run_id, branch, commit_message, commit_sha, status,
            root_cause=None, explanation=None, suggested_fix=None,
            severity=None, auto_fixable=None, self_heal_action=None,
            created_at=None):
    """Ek pipeline run ka data database me save karo"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO pipeline_runs (
            run_id, branch, commit_message, commit_sha, status,
            root_cause, explanation, suggested_fix, severity,
            auto_fixable, self_heal_action, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        run_id, branch, commit_message, commit_sha, status,
        root_cause, explanation, suggested_fix, severity,
        auto_fixable, self_heal_action, created_at
    ))

    conn.commit()
    conn.close()
    print(f"💾 Run {run_id} database me log ho gaya.")