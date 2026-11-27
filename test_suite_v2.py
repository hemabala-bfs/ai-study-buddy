"""
AI Study Buddy V2.0 - Comprehensive Test Suite
================================================
Automated testing for DatabaseManager, StudyRecommendationEngine,
PerformanceAnalyzer, AdaptiveQuizEngine, and Flask API endpoints.
"""

import os
import sys
import json
import unittest
import tempfile
import sqlite3

# Ensure current directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from ml_engine import StudyRecommendationEngine, PerformanceAnalyzer, AdaptiveQuizEngine
from app import app


class TestDatabaseManager(unittest.TestCase):
    """Test suite for SQLite DatabaseManager operations."""

    def setUp(self):
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix='.db')
        os.close(self.temp_db_fd)
        self.db = DatabaseManager(self.temp_db_path)
        self.db.init_db()

    def tearDown(self):
        if os.path.exists(self.temp_db_path):
            try:
                os.remove(self.temp_db_path)
            except OSError:
                pass

    def test_init_db_creates_tables(self):
        """Verify that all required tables are initialized."""
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        required_tables = ['users', 'quiz_attempts', 'study_sessions', 'learning_goals', 'resource_bookmarks']
        for tbl in required_tables:
            self.assertIn(tbl, tables, f"Table {tbl} must exist")
        print("✓ test_init_db_creates_tables: PASSED")

    def test_default_user_created(self):
        """Verify default student user is seeded."""
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username FROM users WHERE id = 1")
        user = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(user)
        self.assertEqual(user[1], 'student')
        print("✓ test_default_user_created: PASSED")

    def test_add_and_get_quiz_attempts(self):
        """Verify quiz attempts are recorded and retrieved."""
        self.db.add_quiz_attempt(1, "Machine Learning", 4, 5, "medium", "[]")
        history = self.db.get_quiz_history(1)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['topic'], "Machine Learning")
        self.assertEqual(history[0]['score'], 4)
        self.assertEqual(history[0]['total_questions'], 5)
        print("✓ test_add_and_get_quiz_attempts: PASSED")

    def test_get_topic_performance(self):
        """Verify aggregated topic statistics."""
        self.db.add_quiz_attempt(1, "Python", 4, 5, "medium")
        self.db.add_quiz_attempt(1, "Python", 5, 5, "hard")
        self.db.add_quiz_attempt(1, "SQL", 2, 5, "easy")

        performance = self.db.get_topic_performance(1)
        self.assertEqual(len(performance), 2)
        python_perf = next(p for p in performance if p['topic'] == 'Python')
        sql_perf = next(p for p in performance if p['topic'] == 'SQL')

        self.assertEqual(python_perf['attempts'], 2)
        self.assertEqual(python_perf['avg_score'], 90.0)
        self.assertEqual(sql_perf['avg_score'], 40.0)
        print("✓ test_get_topic_performance: PASSED")

    def test_study_sessions_and_stats(self):
        """Verify recording study sessions and calculating stats."""
        self.db.add_study_session(1, "Neural Networks", "concept_explainer", 1800)
        self.db.add_study_session(1, "Python OOP", "notes_generator", 1800)
        self.db.add_quiz_attempt(1, "Neural Networks", 4, 5, "medium")

        stats = self.db.get_study_stats(1)
        self.assertEqual(stats['total_quizzes'], 1)
        self.assertEqual(stats['total_sessions'], 2)
        self.assertEqual(stats['total_study_seconds'], 3600)
        self.assertEqual(stats['total_study_hours'], 1.0)
        self.assertEqual(stats['average_score'], 80.0)
        print("✓ test_study_sessions_and_stats: PASSED")

    def test_overall_analytics_payload(self):
        """Verify complete analytics dictionary structure."""
        self.db.add_quiz_attempt(1, "Linear Regression", 5, 5, "medium")
        self.db.add_quiz_attempt(1, "Databases", 2, 5, "medium")
        analytics = self.db.get_overall_analytics(1)

        self.assertIn('stats', analytics)
        self.assertIn('learning_streak', analytics)
        self.assertIn('topic_performance', analytics)
        self.assertIn('recent_activity', analytics)
        self.assertIn('strengths', analytics)
        self.assertIn('weaknesses', analytics)
        self.assertTrue(any(s['topic'] == 'Linear Regression' for s in analytics['strengths']))
        self.assertTrue(any(w['topic'] == 'Databases' for w in analytics['weaknesses']))
        print("✓ test_overall_analytics_payload: PASSED")


class TestStudyRecommendationEngine(unittest.TestCase):
    """Test suite for Scikit-learn TF-IDF & Cosine Similarity Recommendation Engine."""

    @classmethod
    def setUpClass(cls):
        cls.engine = StudyRecommendationEngine()

    def test_vectorizer_and_matrix_initialization(self):
        """Verify TF-IDF matrix is created with features."""
        self.assertIsNotNone(self.engine.tfidf_matrix)
        self.assertGreater(self.engine.tfidf_matrix.shape[0], 0)
        self.assertGreater(self.engine.tfidf_matrix.shape[1], 0)
        print(f"✓ test_vectorizer_and_matrix_initialization: PASSED (Shape: {self.engine.tfidf_matrix.shape})")

    def test_recommend_resources_ml_query(self):
        """Verify recommendation relevance for Machine Learning queries."""
        recs = self.engine.recommend_resources("deep learning and backpropagation", n=5)
        self.assertGreater(len(recs), 0)
        self.assertIn('similarity_score', recs[0])
        self.assertGreaterEqual(recs[0]['similarity_score'], 0.0)
        self.assertLessEqual(recs[0]['similarity_score'], 1.0)
        # Top result should be in Machine Learning
        self.assertEqual(recs[0]['category'], 'Machine Learning')
        print(f"✓ test_recommend_resources_ml_query: PASSED (Top: '{recs[0]['title']}', Score: {recs[0]['similarity_score']})")

    def test_recommend_resources_python_query(self):
        """Verify recommendations for Python-specific topics."""
        recs = self.engine.recommend_resources("python data structures lists and dictionaries", n=3)
        self.assertGreater(len(recs), 0)
        self.assertEqual(recs[0]['category'], 'Python Programming')
        print(f"✓ test_recommend_resources_python_query: PASSED (Top: '{recs[0]['title']}')")

    def test_recommend_with_difficulty_filter(self):
        """Verify difficulty filtering in recommendation engine."""
        recs = self.engine.recommend_resources("machine learning", difficulty="beginner", n=5)
        for r in recs:
            self.assertEqual(r['difficulty'], 'beginner')
        print("✓ test_recommend_with_difficulty_filter: PASSED")

    def test_empty_query_handling(self):
        """Verify graceful handling of blank queries."""
        self.assertEqual(self.engine.recommend_resources(""), [])
        self.assertEqual(self.engine.recommend_resources("   "), [])
        print("✓ test_empty_query_handling: PASSED")

    def test_model_info_and_evaluation(self):
        """Verify genuine evaluation metrics calculation."""
        info = self.engine.get_model_info()
        self.assertEqual(info['vectorizer'], 'TfidfVectorizer')
        self.assertEqual(info['similarity_metric'], 'Cosine Similarity')
        self.assertIn('limitations', info)

        eval_results = self.engine.evaluate_recommendations()
        self.assertIn('mean_precision_at_5', eval_results)
        self.assertIn('mean_reciprocal_rank', eval_results)
        self.assertGreater(eval_results['mean_precision_at_5'], 0.5)
        self.assertGreater(eval_results['mean_reciprocal_rank'], 0.5)
        print(f"✓ test_model_info_and_evaluation: PASSED (P@5: {eval_results['mean_precision_at_5']}, MRR: {eval_results['mean_reciprocal_rank']})")


class TestPerformanceAnalyzerAndAdaptiveQuiz(unittest.TestCase):
    """Test suite for PerformanceAnalyzer and AdaptiveQuizEngine."""

    def setUp(self):
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix='.db')
        os.close(self.temp_db_fd)
        self.db = DatabaseManager(self.temp_db_path)
        self.db.init_db()
        self.analyzer = PerformanceAnalyzer(self.temp_db_path)
        self.adaptive = AdaptiveQuizEngine(self.temp_db_path)

    def tearDown(self):
        if os.path.exists(self.temp_db_path):
            try:
                os.remove(self.temp_db_path)
            except OSError:
                pass

    def test_adaptive_difficulty_selection(self):
        """Verify difficulty adjusts dynamically according to score thresholds."""
        # Untested topic defaults to medium
        self.assertEqual(self.adaptive.select_difficulty(1, "New Topic"), "medium")

        # High scoring topic (>=80%) escalates to hard
        self.db.add_quiz_attempt(1, "Calculus", 5, 5, "medium")
        self.db.add_quiz_attempt(1, "Calculus", 4, 5, "medium")
        self.assertEqual(self.adaptive.select_difficulty(1, "Calculus"), "hard")

        # Low scoring topic (<50%) falls back to easy
        self.db.add_quiz_attempt(1, "Compilers", 1, 5, "medium")
        self.assertEqual(self.adaptive.select_difficulty(1, "Compilers"), "easy")
        print("✓ test_adaptive_difficulty_selection: PASSED")

    def test_adaptive_scoring_multiplier(self):
        """Verify weighting multiplier based on question difficulty."""
        easy_res = self.adaptive.calculate_adaptive_score({'score': 5, 'total': 5}, 'easy')
        hard_res = self.adaptive.calculate_adaptive_score({'score': 5, 'total': 5}, 'hard')
        self.assertEqual(easy_res['difficulty_multiplier'], 0.8)
        self.assertEqual(hard_res['difficulty_multiplier'], 1.3)
        print("✓ test_adaptive_scoring_multiplier: PASSED")

    def test_personalized_study_plan_generation(self):
        """Verify study plan prioritizes weak topics."""
        self.db.add_quiz_attempt(1, "Weak Topic A", 1, 5, "medium")
        self.db.add_quiz_attempt(1, "Strong Topic B", 5, 5, "medium")

        engine = StudyRecommendationEngine()
        plan = self.analyzer.generate_study_plan(1, engine)
        self.assertGreater(len(plan), 0)
        # Weak topic must have high priority
        self.assertEqual(plan[0]['priority'], 'high')
        self.assertEqual(plan[0]['topic'], "Weak Topic A")
        self.assertGreater(len(plan[0]['resources']), 0)
        print("✓ test_personalized_study_plan_generation: PASSED")


class TestFlaskAPIRoutesV2(unittest.TestCase):
    """Test suite for all Flask web endpoints."""

    def setUp(self):
        app.testing = True
        self.client = app.test_client()

    def test_frontend_routes(self):
        """Verify homepage and V2 dashboard HTML routes load."""
        resp_home = self.client.get("/")
        self.assertEqual(resp_home.status_code, 200)

        resp_dash = self.client.get("/dashboard")
        self.assertEqual(resp_dash.status_code, 200)
        self.assertIn(b"AI Study Buddy V2.0", resp_dash.data)
        print("✓ test_frontend_routes: PASSED (GET / and GET /dashboard)")

    def test_status_endpoint(self):
        """Verify V2.0 status payload."""
        resp = self.client.get("/api/status")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data['status'], 'online')
        self.assertEqual(data['version'], '2.0')
        self.assertEqual(data['ml_engine'], 'active')
        print("✓ test_status_endpoint: PASSED")

    def test_recommendations_endpoint(self):
        """Verify recommendations endpoint handles valid and missing params."""
        # Valid query
        resp = self.client.get("/api/recommendations?topic=machine+learning&n=3")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(len(data['recommendations']), 3)

        # Missing query
        resp_err = self.client.get("/api/recommendations")
        self.assertEqual(resp_err.status_code, 400)
        print("✓ test_recommendations_endpoint: PASSED")

    def test_model_info_endpoint(self):
        """Verify ML model info and evaluation endpoint."""
        resp = self.client.get("/api/model-info")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn('model', data)
        self.assertIn('evaluation', data)
        print("✓ test_model_info_endpoint: PASSED")

    def test_analytics_and_progress_endpoints(self):
        """Verify analytics and progress data endpoints."""
        resp_a = self.client.get("/api/analytics")
        self.assertEqual(resp_a.status_code, 200)

        resp_p = self.client.get("/api/progress/topics")
        self.assertEqual(resp_p.status_code, 200)
        print("✓ test_analytics_and_progress_endpoints: PASSED")

    def test_quiz_submit_and_session_track(self):
        """Verify submitting quiz results and tracking sessions."""
        quiz_payload = {
            "topic": "Python Fundamentals",
            "score": 4,
            "total": 5,
            "difficulty": "medium",
            "questions": []
        }
        resp_q = self.client.post("/api/quiz/submit", json=quiz_payload)
        self.assertEqual(resp_q.status_code, 200)
        data_q = resp_q.get_json()
        self.assertTrue(data_q['saved'])
        self.assertIn('adaptive_score', data_q)

        session_payload = {
            "topic": "Python Fundamentals",
            "feature_used": "interactive_quiz",
            "duration": 180
        }
        resp_s = self.client.post("/api/session/track", json=session_payload)
        self.assertEqual(resp_s.status_code, 200)
        self.assertTrue(resp_s.get_json()['tracked'])
        print("✓ test_quiz_submit_and_session_track: PASSED")

    def test_empty_input_validations_preserved(self):
        """Verify that legacy endpoints still reject empty inputs properly."""
        endpoints = [
            ("/explain", {"topic": ""}),
            ("/notes", {"topic": ""}),
            ("/quiz", {"topic": ""}),
            ("/code", {"query": ""}),
            ("/api/quiz/adaptive", {"topic": ""})
        ]
        for url, payload in endpoints:
            resp = self.client.post(url, json=payload)
            self.assertEqual(resp.status_code, 400)
        print("✓ test_empty_input_validations_preserved: PASSED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
