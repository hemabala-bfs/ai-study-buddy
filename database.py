"""
AI Study Buddy V2.0 - Database Manager
=======================================
SQLite database layer for persistent storage of quiz attempts,
study sessions, learning goals, and user analytics.

Author: hemabala-bfs
"""

import sqlite3
import os
from datetime import datetime, timedelta


class DatabaseManager:
    """Manages SQLite database operations for AI Study Buddy V2.0."""

    def __init__(self, db_path='study_buddy.db'):
        self.db_path = db_path

    def _get_conn(self):
        """Get a new database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def init_db(self):
        """Initialize all database tables and seed default data."""
        conn = self._get_conn()
        try:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    email TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS quiz_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    topic TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    total_questions INTEGER NOT NULL,
                    difficulty TEXT DEFAULT 'medium',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    questions_json TEXT DEFAULT '[]',
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );

                CREATE TABLE IF NOT EXISTS study_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    topic TEXT NOT NULL,
                    feature_used TEXT NOT NULL,
                    duration_seconds INTEGER DEFAULT 0,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );

                CREATE TABLE IF NOT EXISTS learning_goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    topic TEXT NOT NULL,
                    target_score INTEGER DEFAULT 80,
                    current_score INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );

                CREATE TABLE IF NOT EXISTS resource_bookmarks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    resource_id INTEGER NOT NULL,
                    topic TEXT DEFAULT '',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );
            ''')

            # Seed default user if not exists
            existing = conn.execute("SELECT id FROM users WHERE id = 1").fetchone()
            if not existing:
                conn.execute(
                    "INSERT INTO users (id, username, email) VALUES (1, 'student', 'student@studybuddy.local')"
                )
            conn.commit()
        finally:
            conn.close()

    def add_quiz_attempt(self, user_id, topic, score, total, difficulty='medium', questions_json='[]'):
        """Record a quiz attempt."""
        conn = self._get_conn()
        try:
            conn.execute(
                """INSERT INTO quiz_attempts (user_id, topic, score, total_questions, difficulty, questions_json)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user_id, topic, score, total, difficulty, questions_json)
            )
            conn.commit()
        finally:
            conn.close()

    def get_quiz_history(self, user_id, limit=50):
        """Retrieve recent quiz attempts for a user."""
        conn = self._get_conn()
        try:
            rows = conn.execute(
                """SELECT id, topic, score, total_questions, difficulty, timestamp
                   FROM quiz_attempts WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?""",
                (user_id, limit)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_topic_performance(self, user_id):
        """Get aggregated performance by topic."""
        conn = self._get_conn()
        try:
            rows = conn.execute(
                """SELECT topic,
                          COUNT(*) as attempts,
                          ROUND(AVG(score * 100.0 / total_questions), 1) as avg_score,
                          MAX(score * 100.0 / total_questions) as best_score,
                          MIN(score * 100.0 / total_questions) as worst_score
                   FROM quiz_attempts
                   WHERE user_id = ?
                   GROUP BY topic
                   ORDER BY avg_score DESC""",
                (user_id,)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def add_study_session(self, user_id, topic, feature_used, duration=0):
        """Record a study session."""
        conn = self._get_conn()
        try:
            conn.execute(
                """INSERT INTO study_sessions (user_id, topic, feature_used, duration_seconds)
                   VALUES (?, ?, ?, ?)""",
                (user_id, topic, feature_used, duration)
            )
            conn.commit()
        finally:
            conn.close()

    def get_study_stats(self, user_id):
        """Get overall study statistics."""
        conn = self._get_conn()
        try:
            quiz_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM quiz_attempts WHERE user_id = ?", (user_id,)
            ).fetchone()['cnt']

            total_time = conn.execute(
                "SELECT COALESCE(SUM(duration_seconds), 0) as total FROM study_sessions WHERE user_id = ?",
                (user_id,)
            ).fetchone()['total']

            session_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM study_sessions WHERE user_id = ?", (user_id,)
            ).fetchone()['cnt']

            avg_score_row = conn.execute(
                """SELECT ROUND(AVG(score * 100.0 / total_questions), 1) as avg
                   FROM quiz_attempts WHERE user_id = ?""",
                (user_id,)
            ).fetchone()
            avg_score = avg_score_row['avg'] if avg_score_row['avg'] is not None else 0

            return {
                'total_quizzes': quiz_count,
                'total_study_seconds': total_time,
                'total_study_hours': round(total_time / 3600, 1),
                'total_sessions': session_count,
                'average_score': avg_score
            }
        finally:
            conn.close()

    def get_learning_streak(self, user_id):
        """Calculate current learning streak in days."""
        conn = self._get_conn()
        try:
            rows = conn.execute(
                """SELECT DISTINCT DATE(timestamp) as day
                   FROM (
                       SELECT timestamp FROM quiz_attempts WHERE user_id = ?
                       UNION ALL
                       SELECT timestamp FROM study_sessions WHERE user_id = ?
                   )
                   ORDER BY day DESC""",
                (user_id, user_id)
            ).fetchall()

            if not rows:
                return 0

            streak = 0
            today = datetime.now().date()
            for row in rows:
                day = datetime.strptime(row['day'], '%Y-%m-%d').date()
                expected = today - timedelta(days=streak)
                if day == expected:
                    streak += 1
                elif day == expected - timedelta(days=1):
                    # Allow one day gap for yesterday
                    streak += 1
                else:
                    break

            return max(streak, 1) if rows else 0
        finally:
            conn.close()

    def get_recent_activity(self, user_id, limit=10):
        """Get recent activity combining quizzes and sessions."""
        conn = self._get_conn()
        try:
            rows = conn.execute(
                """SELECT 'quiz' as type, topic, 
                          'Scored ' || score || '/' || total_questions as detail,
                          timestamp
                   FROM quiz_attempts WHERE user_id = ?
                   UNION ALL
                   SELECT 'session' as type, topic,
                          feature_used || ' (' || duration_seconds || 's)' as detail,
                          timestamp
                   FROM study_sessions WHERE user_id = ?
                   ORDER BY timestamp DESC LIMIT ?""",
                (user_id, user_id, limit)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_weekly_progress(self, user_id):
        """Get daily quiz performance for the last 7 days."""
        conn = self._get_conn()
        try:
            rows = conn.execute(
                """SELECT DATE(timestamp) as day,
                          COUNT(*) as quizzes,
                          ROUND(AVG(score * 100.0 / total_questions), 1) as avg_score
                   FROM quiz_attempts
                   WHERE user_id = ? AND timestamp >= DATE('now', '-7 days')
                   GROUP BY DATE(timestamp)
                   ORDER BY day ASC""",
                (user_id,)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_feature_usage(self, user_id):
        """Get usage count by feature type."""
        conn = self._get_conn()
        try:
            rows = conn.execute(
                """SELECT feature_used, COUNT(*) as count
                   FROM study_sessions WHERE user_id = ?
                   GROUP BY feature_used
                   ORDER BY count DESC""",
                (user_id,)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_overall_analytics(self, user_id):
        """Return comprehensive analytics for the dashboard."""
        stats = self.get_study_stats(user_id)
        streak = self.get_learning_streak(user_id)
        topic_perf = self.get_topic_performance(user_id)
        recent = self.get_recent_activity(user_id)
        weekly = self.get_weekly_progress(user_id)
        feature_usage = self.get_feature_usage(user_id)

        # Determine strengths and weaknesses
        strengths = [t for t in topic_perf if t['avg_score'] >= 70]
        weaknesses = [t for t in topic_perf if t['avg_score'] < 70]

        return {
            'stats': stats,
            'learning_streak': streak,
            'topic_performance': topic_perf,
            'recent_activity': recent,
            'weekly_progress': weekly,
            'feature_usage': feature_usage,
            'strengths': strengths,
            'weaknesses': weaknesses
        }
