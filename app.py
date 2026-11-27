import os
import json
import logging
from flask import Flask, render_template, request, jsonify

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Load environment variables safely
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logging.info("python-dotenv not installed. Reading .env manually if available.")
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))

# Attempt SDK imports with multi-level fallbacks
genai_client = None
genai_sdk_mode = None

# 1. Modern google-genai SDK
try:
    from google import genai
    genai_sdk_mode = "google-genai"
    logging.info("Detected google-genai SDK.")
except ImportError:
    pass

# 2. Classic google-generativeai SDK
if not genai_sdk_mode:
    try:
        import google.generativeai as classic_genai
        genai_sdk_mode = "google-generativeai"
        logging.info("Detected google-generativeai SDK.")
    except ImportError:
        pass

# ==================================================================
# V2.0 Imports: ML Engine & Database
# ==================================================================
from database import DatabaseManager
from ml_engine import StudyRecommendationEngine, PerformanceAnalyzer, AdaptiveQuizEngine

app = Flask(__name__)

# ==================================================================
# V2.0 Initialization: Database & ML Models
# ==================================================================
db = DatabaseManager()
db.init_db()
recommendation_engine = StudyRecommendationEngine()
performance_analyzer = PerformanceAnalyzer(db.db_path)
adaptive_quiz = AdaptiveQuizEngine(db.db_path)

logging.info("V2.0 ML engine and database initialized successfully.")


def get_gemini_api_key():
    """Retrieve Gemini API key from environment variables."""
    return os.environ.get("GEMINI_API_KEY", "").strip()

def call_gemini_api(prompt: str) -> dict:
    """
    Call Gemini API using official SDK or standard library REST fallback.
    Returns a dictionary: {"success": bool, "text": str, "error": str}
    """
    api_key = get_gemini_api_key()
    if not api_key or api_key == "your_gemini_api_key_here":
        return {
            "success": False,
            "text": "",
            "error": "GEMINI_API_KEY is not configured. Please add your Gemini API key to the .env file."
        }

    # Approach A: Modern google-genai SDK
    if genai_sdk_mode == "google-genai":
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt
            )
            return {"success": True, "text": response.text.strip(), "error": None}
        except Exception as e:
            logging.error(f"google-genai call failed: {e}")
            return {"success": False, "text": "", "error": f"Gemini API error: {str(e)}"}

    # Approach B: Classic google-generativeai SDK
    elif genai_sdk_mode == "google-generativeai":
        try:
            classic_genai.configure(api_key=api_key)
            model = classic_genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            return {"success": True, "text": response.text.strip(), "error": None}
        except Exception as e:
            logging.error(f"google-generativeai call failed: {e}")
            return {"success": False, "text": "", "error": f"Gemini API error: {str(e)}"}

    # Approach C: Standard Library REST fallback (zero extra dependencies required)
    else:
        try:
            import urllib.request
            import urllib.error
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            payload = json.dumps({
                "contents": [{"parts": [{"text": prompt}]}]
            }).encode("utf-8")
            
            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return {"success": True, "text": parts[0].get("text", "").strip(), "error": None}
                return {"success": False, "text": "", "error": "No response text received from Gemini API."}
        except urllib.error.HTTPError as http_err:
            try:
                err_body = json.loads(http_err.read().decode("utf-8"))
                msg = err_body.get("error", {}).get("message", str(http_err))
            except Exception:
                msg = str(http_err)
            return {"success": False, "text": "", "error": f"Gemini HTTP Error: {msg}"}
        except Exception as e:
            logging.error(f"REST fallback call failed: {e}")
            return {"success": False, "text": "", "error": f"Network error: {str(e)}"}


# =====================================================================
# ORIGINAL ROUTES (Module 5 - Preserved)
# =====================================================================

@app.route("/")
def index():
    """Render the main study tools interface (Module 5)."""
    return render_template("index.html")

@app.route("/api/status", methods=["GET"])
def api_status():
    """Health check endpoint and API key verification."""
    api_key = get_gemini_api_key()
    has_key = bool(api_key and api_key != "your_gemini_api_key_here")
    return jsonify({
        "status": "online",
        "version": "2.0",
        "has_api_key": has_key,
        "sdk_mode": genai_sdk_mode or "rest-fallback",
        "ml_engine": "active",
        "database": "active"
    })

@app.route("/explain", methods=["POST"])
def explain():
    """1. AI Concept Explainer Endpoint"""
    data = request.get_json() or {}
    topic = data.get("topic", "").strip()
    if not topic:
        return jsonify({"error": "Please enter an academic topic to explain."}), 400

    # V2.0: Track study session
    db.add_study_session(1, topic, 'concept_explainer', 0)

    prompt = (
        f"You are an expert academic tutor. Explain the following topic in simple, beginner-friendly language:\n\n"
        f"Topic: {topic}\n\n"
        f"Structure your explanation with:\n"
        f"1. A clear high-level summary (What is it?)\n"
        f"2. Core Concepts & How It Works\n"
        f"3. Real-World Example / Analogy\n"
        f"4. Key Takeaways\n"
        f"Keep the tone encouraging, clear, and easy to understand."
    )
    result = call_gemini_api(prompt)
    if not result["success"]:
        return jsonify({"error": result["error"]}), 503
    return jsonify({"result": result["text"]})

@app.route("/notes", methods=["POST"])
def notes():
    """2. AI Notes Generator Endpoint"""
    data = request.get_json() or {}
    topic = data.get("topic", "").strip()
    if not topic:
        return jsonify({"error": "Please enter a topic for notes generation."}), 400

    # V2.0: Track study session
    db.add_study_session(1, topic, 'notes_generator', 0)

    prompt = (
        f"Create structured, high-yield revision study notes on the topic:\n\n"
        f"Topic: {topic}\n\n"
        f"Format the notes using clean markdown with:\n"
        f"• Overview & Definition\n"
        f"• Key Formulas / Rules / Terminology\n"
        f"• Important Subtopics with Bullet Summaries\n"
        f"• Common Pitfalls or Exam Tips\n"
        f"• Quick 3-bullet Recap\n"
        f"Make the notes concise, organized, and ideal for fast revision."
    )
    result = call_gemini_api(prompt)
    if not result["success"]:
        return jsonify({"error": result["error"]}), 503
    return jsonify({"result": result["text"]})

@app.route("/quiz", methods=["POST"])
def quiz():
    """3. AI Quiz Generator Endpoint"""
    data = request.get_json() or {}
    topic = data.get("topic", "").strip()
    if not topic:
        return jsonify({"error": "Please enter a topic for quiz generation."}), 400

    prompt = (
        f"Generate a 5-question multiple-choice quiz on the topic: '{topic}'.\n"
        f"Respond ONLY with a valid JSON array of objects. Do not include markdown code block formatting (like ```json), just raw JSON.\n"
        f"Each object must have exactly these keys:\n"
        f"- 'question': string containing the question\n"
        f"- 'options': array of 4 string choices (e.g. ['A) option 1', 'B) option 2', 'C) option 3', 'D) option 4'])\n"
        f"- 'answer': string matching the exact correct option string (e.g. 'A) option 1')\n"
        f"- 'explanation': brief 1-2 sentence explanation of why this answer is correct.\n"
    )
    result = call_gemini_api(prompt)
    if not result["success"]:
        return jsonify({"error": result["error"]}), 503

    raw_text = result["text"]
    # Clean possible markdown wrapping if the model outputs ```json ... ```
    if raw_text.startswith("```"):
        lines = raw_text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        raw_text = "\n".join(lines).strip()

    try:
        quiz_data = json.loads(raw_text)
        return jsonify({"quiz": quiz_data})
    except json.JSONDecodeError as err:
        logging.error(f"Failed to parse quiz JSON: {err}. Raw output was: {raw_text}")
        return jsonify({
            "error": "The AI response could not be parsed as a structured quiz. Please try again.",
            "raw": raw_text
        }), 502

@app.route("/code", methods=["POST"])
def code_assist():
    """4. AI Coding Assistant Endpoint"""
    data = request.get_json() or {}
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"error": "Please enter a programming question or code snippet."}), 400

    # V2.0: Track study session
    db.add_study_session(1, 'Programming', 'coding_assistant', 0)

    prompt = (
        f"You are a patient and knowledgeable programming mentor.\n"
        f"User query:\n{query}\n\n"
        f"Please provide:\n"
        f"1. Explanation of the core concept or bug\n"
        f"2. Correct, clean, well-commented code snippet\n"
        f"3. Line-by-line explanation of the solution\n"
        f"4. Best practice tip for writing maintainable code\n"
        f"Keep the language beginner-friendly and encouraging."
    )
    result = call_gemini_api(prompt)
    if not result["success"]:
        return jsonify({"error": result["error"]}), 503
    return jsonify({"result": result["text"]})


# =====================================================================
# V2.0 NEW ROUTES: Dashboard, Analytics, Recommendations, Study Plans
# =====================================================================

@app.route("/dashboard")
def dashboard():
    """Render the V2.0 analytics dashboard."""
    return render_template("dashboard.html")


@app.route("/api/analytics", methods=["GET"])
def api_analytics():
    """Comprehensive analytics data for the dashboard."""
    try:
        user_id = request.args.get('user_id', 1, type=int)
        analytics = db.get_overall_analytics(user_id)
        return jsonify(analytics)
    except Exception as e:
        logging.error(f"Analytics error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/recommendations", methods=["GET"])
def api_recommendations():
    """Get ML-powered study resource recommendations."""
    topic = request.args.get('topic', '').strip()
    difficulty = request.args.get('difficulty', None)
    n = request.args.get('n', 5, type=int)

    if not topic:
        return jsonify({"error": "Please provide a topic parameter."}), 400

    try:
        recommendations = recommendation_engine.recommend_resources(topic, difficulty=difficulty, n=n)
        return jsonify({
            "topic": topic,
            "count": len(recommendations),
            "recommendations": recommendations
        })
    except Exception as e:
        logging.error(f"Recommendation error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/study-plan", methods=["POST"])
def api_study_plan():
    """Generate a personalized study plan."""
    try:
        user_id = 1
        plan = performance_analyzer.generate_study_plan(user_id, recommendation_engine)
        return jsonify({"plan": plan})
    except Exception as e:
        logging.error(f"Study plan error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/quiz/adaptive", methods=["POST"])
def api_adaptive_quiz():
    """Generate an adaptive quiz with difficulty based on performance."""
    data = request.get_json() or {}
    topic = data.get("topic", "").strip()
    if not topic:
        return jsonify({"error": "Please provide a topic."}), 400

    user_id = data.get("user_id", 1)

    # Determine difficulty based on past performance
    difficulty = adaptive_quiz.select_difficulty(user_id, topic)

    difficulty_prompts = {
        'easy': 'Create basic recall-level questions suitable for beginners.',
        'medium': 'Create moderate application-level questions for intermediate students.',
        'hard': 'Create challenging analysis and synthesis-level questions for advanced students.'
    }

    prompt = (
        f"Generate a 5-question multiple-choice quiz on '{topic}' at {difficulty} difficulty level.\n"
        f"{difficulty_prompts.get(difficulty, '')}\n"
        f"Respond ONLY with a valid JSON array. No markdown formatting.\n"
        f"Each object: 'question' (str), 'options' (array of 4 strings like 'A) ...'), "
        f"'answer' (exact match), 'explanation' (1-2 sentences).\n"
    )

    result = call_gemini_api(prompt)
    if not result["success"]:
        return jsonify({"error": result["error"], "difficulty": difficulty}), 503

    raw_text = result["text"]
    if raw_text.startswith("```"):
        lines = raw_text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        raw_text = "\n".join(lines).strip()

    try:
        quiz_data = json.loads(raw_text)
        return jsonify({
            "quiz": quiz_data,
            "difficulty": difficulty,
            "topic": topic
        })
    except json.JSONDecodeError:
        return jsonify({"error": "Failed to parse quiz response.", "difficulty": difficulty}), 502


@app.route("/api/quiz/submit", methods=["POST"])
def api_quiz_submit():
    """Submit quiz results and update performance tracking."""
    data = request.get_json() or {}
    topic = data.get("topic", "").strip()
    score = data.get("score", 0)
    total = data.get("total", 5)
    difficulty = data.get("difficulty", "medium")
    questions_json = json.dumps(data.get("questions", []))

    if not topic:
        return jsonify({"error": "Topic is required."}), 400

    try:
        user_id = 1
        db.add_quiz_attempt(user_id, topic, score, total, difficulty, questions_json)

        # Calculate adaptive score
        adaptive_result = adaptive_quiz.calculate_adaptive_score(
            {'score': score, 'total': total}, difficulty
        )

        # Get updated mastery
        mastery = performance_analyzer.predict_mastery_level(user_id, topic)

        # Next difficulty suggestion
        next_difficulty = adaptive_quiz.select_difficulty(user_id, topic)

        return jsonify({
            "saved": True,
            "adaptive_score": adaptive_result,
            "mastery": mastery,
            "next_difficulty": next_difficulty
        })
    except Exception as e:
        logging.error(f"Quiz submit error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/session/track", methods=["POST"])
def api_session_track():
    """Track a study session."""
    data = request.get_json() or {}
    topic = data.get("topic", "general").strip()
    feature = data.get("feature_used", "unknown").strip()
    duration = data.get("duration", 0)

    try:
        db.add_study_session(1, topic, feature, duration)
        return jsonify({"tracked": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/progress/topics", methods=["GET"])
def api_progress_topics():
    """Get per-topic learning progress."""
    try:
        user_id = request.args.get('user_id', 1, type=int)
        topic_scores = performance_analyzer.calculate_topic_scores(user_id)
        progress_data = performance_analyzer.get_learning_progress(user_id)
        return jsonify({
            "topic_scores": topic_scores,
            "progress_timeline": progress_data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/model-info", methods=["GET"])
def api_model_info():
    """Return ML model metadata and evaluation results."""
    try:
        info = recommendation_engine.get_model_info()
        evaluation = recommendation_engine.evaluate_recommendations()
        return jsonify({
            "model": info,
            "evaluation": evaluation
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/resources/search", methods=["GET"])
def api_resource_search():
    """Search and filter study resources."""
    query = request.args.get('q', '').strip()
    category = request.args.get('category', None)
    difficulty = request.args.get('difficulty', None)

    try:
        results = recommendation_engine.search_resources(query, category, difficulty)
        return jsonify({
            "query": query,
            "count": len(results),
            "resources": results[:20]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logging.info(f"Starting AI Study Buddy V2.0 on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
