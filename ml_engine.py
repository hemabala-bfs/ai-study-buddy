"""
AI Study Buddy V2.0 - Machine Learning Engine
===============================================
Implements genuine ML algorithms for study resource recommendations,
performance analysis, and adaptive quiz difficulty selection.

ML Techniques Used:
- TF-IDF Vectorization (text feature extraction)
- Cosine Similarity (content-based recommendation)
- KMeans Clustering (topic grouping)
- StandardScaler (feature normalization)

Author: hemabala-bfs
"""

import json
import os
import sqlite3
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from datetime import datetime, timedelta


class StudyRecommendationEngine:
    """
    Content-based study resource recommendation engine using TF-IDF
    vectorization and cosine similarity.

    ML Methodology:
    ----------------
    1. Text Representation: Each study resource's description + tags are
       combined into a single text document.
    2. TF-IDF Vectorization: Documents are converted to TF-IDF vectors
       using unigrams and bigrams (ngram_range=(1,2)), which captures
       both individual terms and meaningful two-word phrases.
    3. Cosine Similarity: User queries are transformed using the same
       vectorizer, and cosine similarity scores are computed against
       all resource vectors to rank relevance.
    4. Topic Clustering: KMeans groups resources into k=5 clusters,
       enabling "related topics" discovery.

    Limitations:
    - Cold-start: New topics with no matching vocabulary in the dataset
      will receive low similarity scores across all resources.
    - Vocabulary-dependent: Recommendations are only as good as the
      textual overlap between query and resource descriptions.
    - No collaborative filtering: Does not use other users' preferences.
    - Static dataset: Resource corpus is fixed at load time.
    """

    def __init__(self, data_path=None):
        if data_path is None:
            data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     'data', 'study_resources.json')
        self.data_path = data_path
        self.resources = self._load_resources()
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=5000,
            stop_words='english',
            sublinear_tf=True  # Apply log normalization to term frequencies
        )
        self.tfidf_matrix = None
        self.cluster_labels = None
        self.scaler = MinMaxScaler()
        self._build_tfidf_matrix()
        self._cluster_resources()

    def _load_resources(self):
        """Load study resources from the JSON dataset."""
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                resources = json.load(f)
            return resources
        except FileNotFoundError:
            # Return minimal fallback dataset
            return [
                {
                    "id": 1, "title": "Python Basics",
                    "description": "Introduction to Python programming language fundamentals",
                    "category": "Python Programming", "difficulty": "beginner",
                    "type": "tutorial", "tags": ["python", "programming"],
                    "estimated_minutes": 30
                }
            ]

    def _build_tfidf_matrix(self):
        """
        Build the TF-IDF matrix from resource descriptions.
        Each document is a combination of title + description + tags
        to maximize textual signal for similarity matching.
        """
        documents = []
        for r in self.resources:
            # Combine multiple text fields for richer representation
            text_parts = [
                r.get('title', ''),
                r.get('description', ''),
                r.get('category', ''),
                ' '.join(r.get('tags', []))
            ]
            documents.append(' '.join(text_parts).lower())

        self.tfidf_matrix = self.vectorizer.fit_transform(documents)

    def _cluster_resources(self):
        """
        Apply KMeans clustering to group similar resources.
        Uses k=5 clusters to discover natural topic groupings.
        """
        if self.tfidf_matrix is not None and self.tfidf_matrix.shape[0] >= 5:
            # Convert sparse to dense for KMeans
            dense_matrix = self.tfidf_matrix.toarray()
            kmeans = KMeans(n_clusters=min(5, len(self.resources)),
                            random_state=42, n_init=10)
            self.cluster_labels = kmeans.fit_predict(dense_matrix)
        else:
            self.cluster_labels = np.zeros(len(self.resources), dtype=int)

    def recommend_resources(self, topic, difficulty=None, n=5):
        """
        Recommend top-N study resources for a given topic using cosine similarity.

        Parameters:
        -----------
        topic : str
            The topic/query to find matching resources for
        difficulty : str, optional
            Filter by difficulty level ('beginner', 'intermediate', 'advanced')
        n : int
            Number of recommendations to return

        Returns:
        --------
        list of dicts with resource info and similarity_score
        """
        if not topic or not topic.strip():
            return []

        # Transform the query using the fitted vectorizer
        query_vec = self.vectorizer.transform([topic.lower()])

        # Compute cosine similarity between query and all resources
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        # Create results with similarity scores
        results = []
        for idx, score in enumerate(similarities):
            resource = self.resources[idx].copy()
            resource['similarity_score'] = round(float(score), 4)
            resource['cluster_id'] = int(self.cluster_labels[idx]) if self.cluster_labels is not None else 0
            results.append(resource)

        # Filter by difficulty if specified
        if difficulty:
            results = [r for r in results if r.get('difficulty') == difficulty]

        # Sort by similarity score descending
        results.sort(key=lambda x: x['similarity_score'], reverse=True)

        return results[:n]

    def get_similarity_scores(self, query):
        """
        Return all similarity scores for analysis/debugging.

        Parameters:
        -----------
        query : str
            The search query

        Returns:
        --------
        list of (resource_title, similarity_score) tuples
        """
        if not query or not query.strip():
            return []

        query_vec = self.vectorizer.transform([query.lower()])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        scores = []
        for idx, score in enumerate(similarities):
            scores.append((self.resources[idx]['title'], round(float(score), 4)))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

    def search_resources(self, query='', category=None, difficulty=None):
        """Search resources with optional filters."""
        results = self.resources.copy()

        if query and query.strip():
            # Use TF-IDF similarity for text search
            query_vec = self.vectorizer.transform([query.lower()])
            similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
            for idx in range(len(results)):
                results[idx] = results[idx].copy()
                results[idx]['similarity_score'] = round(float(similarities[idx]), 4)
            # Filter out zero-similarity results
            results = [r for r in results if r['similarity_score'] > 0.01]
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
        else:
            for r in results:
                r['similarity_score'] = 0.0

        if category:
            results = [r for r in results if r.get('category', '').lower() == category.lower()]

        if difficulty:
            results = [r for r in results if r.get('difficulty', '') == difficulty]

        return results

    def evaluate_recommendations(self, test_queries=None):
        """
        Evaluate the recommendation system using test queries.
        Returns precision-based metrics.

        This is an intrinsic evaluation: for each test query that belongs
        to a known category, we check whether the top-5 recommendations
        contain resources from the same category.

        Returns:
        --------
        dict with evaluation metrics
        """
        if test_queries is None:
            test_queries = [
                {"query": "neural networks deep learning", "expected_category": "Machine Learning"},
                {"query": "python programming classes objects", "expected_category": "Python Programming"},
                {"query": "SQL database queries joins", "expected_category": "Database Systems"},
                {"query": "HTML CSS responsive web design", "expected_category": "Web Development"},
                {"query": "probability statistics distributions", "expected_category": "Mathematics"},
                {"query": "operating system processes threads", "expected_category": "Computer Science"},
                {"query": "pandas dataframes data analysis", "expected_category": "Data Science"},
            ]

        results = {
            'queries_tested': len(test_queries),
            'per_query': [],
            'mean_precision_at_5': 0.0,
            'mean_reciprocal_rank': 0.0
        }

        precisions = []
        reciprocal_ranks = []

        for tq in test_queries:
            recs = self.recommend_resources(tq['query'], n=5)
            relevant_count = sum(1 for r in recs
                                 if r.get('category') == tq['expected_category'])
            precision = relevant_count / len(recs) if recs else 0

            # Mean Reciprocal Rank
            rr = 0
            for i, r in enumerate(recs):
                if r.get('category') == tq['expected_category']:
                    rr = 1.0 / (i + 1)
                    break

            precisions.append(precision)
            reciprocal_ranks.append(rr)

            results['per_query'].append({
                'query': tq['query'],
                'expected_category': tq['expected_category'],
                'precision_at_5': round(precision, 3),
                'reciprocal_rank': round(rr, 3),
                'top_results': [{'title': r['title'], 'category': r.get('category', ''),
                                 'score': r['similarity_score']} for r in recs[:3]]
            })

        results['mean_precision_at_5'] = round(np.mean(precisions), 3) if precisions else 0
        results['mean_reciprocal_rank'] = round(np.mean(reciprocal_ranks), 3) if reciprocal_ranks else 0

        return results

    def get_model_info(self):
        """Return metadata about the ML model."""
        feature_names = self.vectorizer.get_feature_names_out()
        return {
            'model_type': 'TF-IDF + Cosine Similarity Content-Based Recommender',
            'vectorizer': 'TfidfVectorizer',
            'ngram_range': '(1, 2)',
            'max_features': 5000,
            'actual_features': len(feature_names),
            'stop_words': 'english',
            'sublinear_tf': True,
            'total_resources': len(self.resources),
            'tfidf_matrix_shape': list(self.tfidf_matrix.shape) if self.tfidf_matrix is not None else None,
            'clustering': 'KMeans (k=5)',
            'similarity_metric': 'Cosine Similarity',
            'categories': list(set(r.get('category', '') for r in self.resources)),
            'limitations': [
                'Cold-start problem for topics with no vocabulary overlap',
                'No collaborative filtering (single-user system)',
                'Static dataset (not updated at runtime)',
                'Text-similarity based, not personalized to learning style'
            ]
        }


class PerformanceAnalyzer:
    """
    Analyzes student quiz performance to identify strengths,
    weaknesses, and generate personalized study plans.

    Uses StandardScaler for normalizing scores across topics,
    enabling fair comparison between topics with different
    score ranges and attempt counts.
    """

    def __init__(self, db_path='study_buddy.db'):
        self.db_path = db_path
        self.scaler = StandardScaler()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def analyze_strengths_weaknesses(self, user_id):
        """
        Identify strong and weak topics based on quiz performance.
        Strength threshold: ≥ 70% average score
        Weakness threshold: < 70% average score

        Returns:
        --------
        dict with 'strengths' and 'weaknesses' lists
        """
        conn = self._get_conn()
        try:
            rows = conn.execute(
                """SELECT topic,
                          COUNT(*) as attempts,
                          AVG(score * 100.0 / total_questions) as avg_pct
                   FROM quiz_attempts WHERE user_id = ?
                   GROUP BY topic""",
                (user_id,)
            ).fetchall()

            strengths = []
            weaknesses = []
            for row in rows:
                entry = {
                    'topic': row['topic'],
                    'avg_score': round(row['avg_pct'], 1),
                    'attempts': row['attempts']
                }
                if row['avg_pct'] >= 70:
                    strengths.append(entry)
                else:
                    weaknesses.append(entry)

            strengths.sort(key=lambda x: x['avg_score'], reverse=True)
            weaknesses.sort(key=lambda x: x['avg_score'])

            return {'strengths': strengths, 'weaknesses': weaknesses}
        finally:
            conn.close()

    def calculate_topic_scores(self, user_id):
        """
        Calculate normalized scores per topic using StandardScaler.
        Returns raw and normalized scores for comparison.
        """
        conn = self._get_conn()
        try:
            rows = conn.execute(
                """SELECT topic,
                          AVG(score * 100.0 / total_questions) as avg_pct,
                          COUNT(*) as attempts
                   FROM quiz_attempts WHERE user_id = ?
                   GROUP BY topic""",
                (user_id,)
            ).fetchall()

            if not rows:
                return {}

            topics = [row['topic'] for row in rows]
            scores = np.array([[row['avg_pct'], row['attempts']] for row in rows])

            if len(scores) >= 2:
                normalized = self.scaler.fit_transform(scores)
            else:
                normalized = scores / 100.0

            result = {}
            for i, topic in enumerate(topics):
                result[topic] = {
                    'raw_score': round(scores[i][0], 1),
                    'attempts': int(scores[i][1]),
                    'normalized_score': round(float(normalized[i][0]), 3)
                }

            return result
        finally:
            conn.close()

    def generate_study_plan(self, user_id, recommendation_engine=None):
        """
        Generate a personalized study plan based on performance analysis.
        Prioritizes weak topics and suggests resources.

        Parameters:
        -----------
        user_id : int
        recommendation_engine : StudyRecommendationEngine, optional
            If provided, includes resource recommendations for each topic

        Returns:
        --------
        list of study plan items with priority, topic, and suggested actions
        """
        analysis = self.analyze_strengths_weaknesses(user_id)
        plan = []

        # Priority 1: Weak topics need immediate attention
        for idx, weak in enumerate(analysis['weaknesses']):
            item = {
                'priority': 'high',
                'day': idx + 1,
                'topic': weak['topic'],
                'current_score': weak['avg_score'],
                'target_score': 80,
                'action': f"Review fundamentals of {weak['topic']}. Take practice quiz at easy level.",
                'estimated_minutes': 45,
                'resources': []
            }
            if recommendation_engine:
                recs = recommendation_engine.recommend_resources(weak['topic'], n=3)
                item['resources'] = [{'title': r['title'], 'type': r.get('type', ''),
                                      'score': r['similarity_score']} for r in recs]
            plan.append(item)

        # Priority 2: Moderate topics need reinforcement
        for idx, strong in enumerate(analysis['strengths']):
            if strong['avg_score'] < 90:
                item = {
                    'priority': 'medium',
                    'day': len(plan) + 1,
                    'topic': strong['topic'],
                    'current_score': strong['avg_score'],
                    'target_score': 95,
                    'action': f"Challenge yourself with advanced {strong['topic']} quiz.",
                    'estimated_minutes': 30,
                    'resources': []
                }
                if recommendation_engine:
                    recs = recommendation_engine.recommend_resources(
                        strong['topic'], difficulty='advanced', n=2)
                    item['resources'] = [{'title': r['title'], 'type': r.get('type', ''),
                                          'score': r['similarity_score']} for r in recs]
                plan.append(item)

        # If no quiz history, suggest exploration
        if not plan:
            plan.append({
                'priority': 'medium',
                'day': 1,
                'topic': 'Getting Started',
                'current_score': 0,
                'target_score': 70,
                'action': 'Start with a quiz on any topic to build your learning profile.',
                'estimated_minutes': 20,
                'resources': []
            })

        return plan

    def get_learning_progress(self, user_id):
        """
        Return time-series data of quiz performance for progress charts.
        Groups by date and shows average score trend.
        """
        conn = self._get_conn()
        try:
            rows = conn.execute(
                """SELECT DATE(timestamp) as date,
                          AVG(score * 100.0 / total_questions) as avg_score,
                          COUNT(*) as quiz_count
                   FROM quiz_attempts WHERE user_id = ?
                   GROUP BY DATE(timestamp)
                   ORDER BY date ASC""",
                (user_id,)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def predict_mastery_level(self, user_id, topic):
        """
        Estimate mastery level for a topic based on historical performance.
        Uses weighted moving average giving more weight to recent attempts.

        Returns:
        --------
        dict with mastery_level, confidence, and recommendation
        """
        conn = self._get_conn()
        try:
            rows = conn.execute(
                """SELECT score, total_questions, timestamp
                   FROM quiz_attempts
                   WHERE user_id = ? AND topic = ?
                   ORDER BY timestamp ASC""",
                (user_id, topic)
            ).fetchall()

            if not rows:
                return {
                    'mastery_level': 'unknown',
                    'score': 0,
                    'confidence': 0,
                    'recommendation': 'No data available. Take a quiz to start tracking.'
                }

            # Weighted moving average: recent scores weigh more
            scores = [r['score'] * 100.0 / r['total_questions'] for r in rows]
            n = len(scores)
            weights = np.arange(1, n + 1, dtype=float)
            weighted_avg = np.average(scores, weights=weights)

            # Determine mastery level
            if weighted_avg >= 90:
                level = 'expert'
                rec = 'Excellent mastery! Try teaching this topic or explore advanced subtopics.'
            elif weighted_avg >= 70:
                level = 'proficient'
                rec = 'Good understanding. Practice advanced questions to reach expert level.'
            elif weighted_avg >= 50:
                level = 'developing'
                rec = 'Making progress. Review weak areas and try more practice quizzes.'
            else:
                level = 'beginner'
                rec = 'Focus on fundamentals. Use the Concept Explainer and study notes.'

            # Confidence based on number of attempts
            confidence = min(n / 5.0, 1.0)  # 5+ attempts = full confidence

            return {
                'mastery_level': level,
                'score': round(weighted_avg, 1),
                'confidence': round(confidence, 2),
                'attempts': n,
                'trend': 'improving' if n >= 2 and scores[-1] > scores[0] else 'stable',
                'recommendation': rec
            }
        finally:
            conn.close()


class AdaptiveQuizEngine:
    """
    Adaptive quiz system that adjusts difficulty based on student performance.

    Algorithm:
    - If average score >= 80%: increase difficulty to 'hard'
    - If average score >= 50%: maintain 'medium' difficulty
    - If average score < 50%: decrease difficulty to 'easy'
    - New topics start at 'medium' difficulty

    Limitations:
    - Difficulty adjustment is based on overall topic score, not per-question analysis
    - Requires at least 1 quiz attempt to adapt (cold start at 'medium')
    - Does not consider time-to-answer or question-level difficulty
    """

    def __init__(self, db_path='study_buddy.db'):
        self.db_path = db_path
        self.difficulty_levels = ['easy', 'medium', 'hard']

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def select_difficulty(self, user_id, topic):
        """
        Select appropriate quiz difficulty based on past performance.

        Returns:
        --------
        str: 'easy', 'medium', or 'hard'
        """
        conn = self._get_conn()
        try:
            row = conn.execute(
                """SELECT AVG(score * 100.0 / total_questions) as avg_pct,
                          COUNT(*) as attempts
                   FROM quiz_attempts
                   WHERE user_id = ? AND topic = ?""",
                (user_id, topic)
            ).fetchone()

            if not row or row['attempts'] == 0 or row['avg_pct'] is None:
                return 'medium'

            avg = row['avg_pct']
            if avg >= 80:
                return 'hard'
            elif avg >= 50:
                return 'medium'
            else:
                return 'easy'
        finally:
            conn.close()

    def calculate_adaptive_score(self, results, difficulty):
        """
        Calculate a weighted score that accounts for question difficulty.

        Parameters:
        -----------
        results : dict with 'score' and 'total' keys
        difficulty : str

        Returns:
        --------
        dict with raw_score, weighted_score, and difficulty_multiplier
        """
        multipliers = {'easy': 0.8, 'medium': 1.0, 'hard': 1.3}
        multiplier = multipliers.get(difficulty, 1.0)

        raw_pct = (results['score'] / results['total'] * 100) if results['total'] > 0 else 0
        weighted = min(raw_pct * multiplier, 100)

        return {
            'raw_score': results['score'],
            'total': results['total'],
            'raw_percentage': round(raw_pct, 1),
            'difficulty': difficulty,
            'difficulty_multiplier': multiplier,
            'weighted_percentage': round(weighted, 1)
        }

    def track_quiz_attempt(self, user_id, topic, score, total, difficulty, questions_json='[]'):
        """Save a quiz attempt to the database."""
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

    def get_difficulty_history(self, user_id, topic):
        """Get the difficulty progression for a topic."""
        conn = self._get_conn()
        try:
            rows = conn.execute(
                """SELECT difficulty, score, total_questions, timestamp
                   FROM quiz_attempts
                   WHERE user_id = ? AND topic = ?
                   ORDER BY timestamp ASC""",
                (user_id, topic)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()


def get_model_info():
    """Convenience function to get ML model info without instantiation."""
    engine = StudyRecommendationEngine()
    return engine.get_model_info()
