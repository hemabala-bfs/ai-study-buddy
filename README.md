# 🎓 AI Study Buddy – Intelligent Learning Assistant

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0.3-000000?style=for-the-badge&logo=flask&logoColor=white)
![Google Gemini](https://img.shields.io/badge/Google%20Gemini-1.5%20Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-Modern-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-Responsive-1572B6?style=for-the-badge&logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)

An intelligent, full-stack learning assistant web application designed to help students learn faster and understand deeper using Artificial Intelligence. Powered by **Python Flask** on the backend and **Google Gemini API** (`gemini-1.5-flash`), with a modern, responsive frontend.

---

## 🌟 Key Features

### 1. 💡 AI Concept Explainer
- Breaks down complex academic topics into simple, beginner-friendly explanations.
- Structured with an overview, core mechanisms, real-world analogies, and key takeaways.

### 2. 📝 AI Notes Generator
- Synthesizes dense topics into high-yield, structured revision notes.
- Highlights definitions, core terminology, exam tips, and quick 3-bullet recaps.

### 3. 🎯 Interactive AI Quiz
- Dynamically generates a 5-question multiple-choice quiz on any topic.
- Provides interactive radio options, real-time score grading, correct answer indicators, and detailed explanations for every question.

### 4. 💻 AI Coding Assistant
- Acts as a patient 1-on-1 programming tutor.
- Diagnoses runtime errors, explains bug causes, provides clean code solutions, and shares best practice recommendations.

### 5. 📱 Modern & Responsive User Interface
- Polished typography using Google Fonts (`Plus Jakarta Sans` & `JetBrains Mono`).
- Smooth tab switching without page reload.
- Real-time API status indicator, button loading spinners, and one-click copy to clipboard.
- Fully responsive across desktop, tablet, and mobile browsers.

---

## 🛠️ Technology Stack

- **Backend:** Python Flask (Routing, Input Validation, JSON APIs)
- **AI Integration:** Google Gemini API (`gemini-1.5-flash`) with multi-tier SDK & native REST fallback
- **Frontend:** Semantic HTML5, Modern CSS3 (Grid & Flexbox), Vanilla JavaScript (Fetch API, DOM manipulation)
- **Environment Management:** `python-dotenv` for secure API credential handling

---

## 📂 Project Directory Structure

```
AI-Study-Buddy/
│
├── app.py                      # Flask application and Gemini API controller
├── requirements.txt            # Python dependencies
├── README.md                   # Comprehensive project documentation
├── .gitignore                  # Git ignore rules (prevents secret leaks)
├── .env.example                # Sample environment configuration
│
├── templates/
│   └── index.html              # Main single-page application dashboard
│
├── static/
│   ├── css/
│   │   └── style.css           # Modern responsive design & animations
│   └── js/
│       └── script.js           # Interactive tabs, fetch requests, & quiz logic
│
├── screenshots/
│   └── README.md               # Screenshot showcase & capture guidelines
│
└── docs/
    ├── AI_Tools_Exploration.md  # In-depth study of ChatGPT, Gemini & Copilot
    └── Project_Documentation.md # System architecture & API specifications
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.9 or higher installed on your computer.
- A free Google Gemini API Key from [Google AI Studio](https://aistudio.google.com/app/apikey).

### 2. Clone or Navigate to the Repository
```bash
git clone https://github.com/YOUR_USERNAME/ai-study-buddy.git
cd ai-study-buddy
```

### 3. Set Up Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate on Windows:
venv\Scripts\activate

# Activate on macOS/Linux:
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Gemini API Key
```bash
# Copy example configuration
cp .env.example .env     # macOS / Linux
copy .env.example .env   # Windows
```
Open `.env` in any text editor and paste your API key:
```env
GEMINI_API_KEY=AIzaSy...your_actual_key_here
```

### 6. Run the Application
```bash
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🧪 Testing and Verification

- **Backend Route Testing:** All routes (`/explain`, `/notes`, `/quiz`, `/code`, `/api/status`) tested via Flask test client with 200 OK responses.
- **Input Validation:** Tested with empty payloads; correctly returns `400 Bad Request` with helpful feedback.
- **Error Handling:** Tested without API key; returns structured `503 Service Unavailable` with setup instructions.
- **Security Audit:** Verified that `.env` is ignored by git to ensure no credentials can be committed.

---

## 🔮 Future Enhancements

- [ ] User authentication with session persistence.
- [ ] Save notes and quiz history to a local SQLite database.
- [ ] Export notes to PDF or Markdown files with one click.
- [ ] Flashcard generator mode with flip animations.

---

## 📜 License
This project is open-source and available under the [MIT License](LICENSE).
