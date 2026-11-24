// ===================================================================
// AI Study Buddy - Frontend Controller
// ===================================================================

document.addEventListener("DOMContentLoaded", () => {
    initTabs();
    initQuickTags();
    checkApiStatus();
    initFormHandlers();
});

// 1. Tab Navigation Logic
function initTabs() {
    const navButtons = document.querySelectorAll(".nav-btn");
    const tabPanels = document.querySelectorAll(".tab-panel");

    navButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const tabId = btn.getAttribute("data-tab");

            navButtons.forEach(b => b.classList.remove("active"));
            tabPanels.forEach(p => p.classList.remove("active"));

            btn.classList.add("active");
            const targetPanel = document.getElementById(`tab-${tabId}`);
            if (targetPanel) {
                targetPanel.classList.add("active");
            }
        });
    });
}

// 2. Quick Topic Tag Pills
function initQuickTags() {
    document.querySelectorAll(".tag-pill").forEach(pill => {
        pill.addEventListener("click", () => {
            const targetId = pill.getAttribute("data-target");
            const inputEl = document.getElementById(targetId);
            if (inputEl) {
                inputEl.value = pill.textContent.trim();
                inputEl.focus();
            }
        });
    });
}

// 3. API Status Checker
async function checkApiStatus() {
    const pill = document.getElementById("apiStatusPill");
    const statusText = pill.querySelector(".status-text");
    const warningBanner = document.getElementById("apiKeyBanner");

    try {
        const resp = await fetch("/api/status");
        const data = await resp.json();

        if (data.has_api_key) {
            pill.className = "api-status-pill online";
            statusText.textContent = `API Ready (${data.sdk_mode})`;
            if (warningBanner) warningBanner.style.display = "none";
        } else {
            pill.className = "api-status-pill offline";
            statusText.textContent = "API Key Missing";
            if (warningBanner) warningBanner.style.display = "flex";
        }
    } catch (e) {
        pill.className = "api-status-pill offline";
        statusText.textContent = "Backend Offline";
    }
}

// 4. Form Submission & API Handlers
function initFormHandlers() {
    // Feature 1: Concept Explainer
    const explainBtn = document.getElementById("explainBtn");
    const explainInput = document.getElementById("explainTopic");
    explainBtn.addEventListener("click", () => {
        handleTextEndpoint({
            url: "/explain",
            payload: { topic: explainInput.value.trim() },
            btn: explainBtn,
            outputBox: document.getElementById("explainOutput"),
            contentBox: document.getElementById("explainContent")
        });
    });
    explainInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") explainBtn.click();
    });

    // Feature 2: Notes Generator
    const notesBtn = document.getElementById("notesBtn");
    const notesInput = document.getElementById("notesTopic");
    notesBtn.addEventListener("click", () => {
        handleTextEndpoint({
            url: "/notes",
            payload: { topic: notesInput.value.trim() },
            btn: notesBtn,
            outputBox: document.getElementById("notesOutput"),
            contentBox: document.getElementById("notesContent")
        });
    });
    notesInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") notesBtn.click();
    });

    // Feature 3: Interactive Quiz
    const quizBtn = document.getElementById("quizBtn");
    const quizInput = document.getElementById("quizTopic");
    quizBtn.addEventListener("click", () => {
        handleQuizGeneration(quizBtn, quizInput.value.trim());
    });
    quizInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") quizBtn.click();
    });

    // Feature 4: Coding Assistant
    const codeBtn = document.getElementById("codeBtn");
    const codeInput = document.getElementById("codeInput");
    codeBtn.addEventListener("click", () => {
        handleTextEndpoint({
            url: "/code",
            payload: { query: codeInput.value.trim() },
            btn: codeBtn,
            outputBox: document.getElementById("codeOutput"),
            contentBox: document.getElementById("codeContent")
        });
    });
}

// Reusable text endpoint runner
async function handleTextEndpoint({ url, payload, btn, outputBox, contentBox }) {
    const textKey = Object.keys(payload)[0];
    if (!payload[textKey]) {
        alert("Please enter an input before submitting!");
        return;
    }

    setLoading(btn, true);
    outputBox.style.display = "block";
    contentBox.innerHTML = '<span style="color: #64748b;">🧠 Thinking and preparing educational response with Gemini...</span>';

    try {
        const resp = await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await resp.json();
        if (!resp.ok) {
            contentBox.innerHTML = `<span style="color: #dc2626; font-weight: 600;">⚠️ Error: ${escapeHtml(data.error || "Unable to process request.")}</span>`;
            return;
        }

        contentBox.textContent = data.result;
    } catch (err) {
        contentBox.innerHTML = `<span style="color: #dc2626; font-weight: 600;">❌ Network Error: Could not connect to the backend server.</span>`;
    } finally {
        setLoading(btn, false);
    }
}

// Global active quiz state
let activeQuizData = [];

// Feature 3: Quiz Generation & Scoring logic
async function handleQuizGeneration(btn, topic) {
    if (!topic) {
        alert("Please enter a topic for the quiz!");
        return;
    }

    const container = document.getElementById("quizContainer");
    const listEl = document.getElementById("quizQuestionsList");
    const scoreResult = document.getElementById("quizScoreResult");
    const resetBtn = document.getElementById("resetQuizBtn");
    const actionsEl = document.getElementById("quizActions");

    setLoading(btn, true);
    container.style.display = "block";
    listEl.innerHTML = '<div style="padding: 1rem; color: #64748b;">⏳ Generating custom 5-question quiz on ' + escapeHtml(topic) + '...</div>';
    scoreResult.style.display = "none";
    resetBtn.style.display = "none";
    actionsEl.style.display = "none";

    try {
        const resp = await fetch("/quiz", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ topic })
        });
        const data = await resp.json();

        if (!resp.ok) {
            listEl.innerHTML = `<div style="padding: 1rem; color: #dc2626; font-weight: 600;">⚠️ ${escapeHtml(data.error || "Failed to generate quiz.")}</div>`;
            return;
        }

        activeQuizData = data.quiz;
        renderQuiz(activeQuizData);
        actionsEl.style.display = "flex";
    } catch (err) {
        listEl.innerHTML = `<div style="padding: 1rem; color: #dc2626;">❌ Network error generating quiz.</div>`;
    } finally {
        setLoading(btn, false);
    }
}

function renderQuiz(questions) {
    const listEl = document.getElementById("quizQuestionsList");
    listEl.innerHTML = "";

    questions.forEach((q, qIndex) => {
        const card = document.createElement("div");
        card.className = "quiz-card";
        card.id = `qCard_${qIndex}`;

        const qText = document.createElement("div");
        qText.className = "quiz-q-text";
        qText.textContent = `Q${qIndex + 1}. ${q.question}`;
        card.appendChild(qText);

        const optionsDiv = document.createElement("div");
        optionsDiv.className = "quiz-options";

        q.options.forEach((opt) => {
            const label = document.createElement("label");
            label.className = "option-label";

            const radio = document.createElement("input");
            radio.type = "radio";
            radio.name = `question_${qIndex}`;
            radio.value = opt;

            label.appendChild(radio);
            label.append(` ${opt}`);
            optionsDiv.appendChild(label);
        });

        card.appendChild(optionsDiv);

        // Hidden explanation element
        const expBox = document.createElement("div");
        expBox.className = "explanation-box";
        expBox.id = `expBox_${qIndex}`;
        expBox.style.display = "none";
        expBox.innerHTML = `<strong>Explanation:</strong> ${escapeHtml(q.explanation || "Correct answer: " + q.answer)}`;
        card.appendChild(expBox);

        listEl.appendChild(card);
    });

    const submitBtn = document.getElementById("submitQuizBtn");
    submitBtn.onclick = evaluateQuiz;
}

function evaluateQuiz() {
    let score = 0;
    let answeredCount = 0;

    activeQuizData.forEach((q, qIndex) => {
        const card = document.getElementById(`qCard_${qIndex}`);
        const selected = card.querySelector(`input[name="question_${qIndex}"]:checked`);
        const labels = card.querySelectorAll(".option-label");
        const expBox = document.getElementById(`expBox_${qIndex}`);

        if (selected) {
            answeredCount++;
            const userChoice = selected.value.trim();
            const correctChoice = q.answer.trim();

            labels.forEach(lbl => {
                const optText = lbl.textContent.trim();
                // Check if this option matches correct
                if (optText === correctChoice || optText.startsWith(correctChoice)) {
                    lbl.classList.add("correct");
                }
                // If user selected this and it was wrong
                if (lbl.contains(selected) && userChoice !== correctChoice) {
                    lbl.classList.add("incorrect");
                }
            });

            if (userChoice === correctChoice || userChoice.startsWith(correctChoice)) {
                score++;
            }
        } else {
            // Highlight the correct one anyway
            labels.forEach(lbl => {
                if (lbl.textContent.trim() === q.answer.trim()) {
                    lbl.classList.add("correct");
                }
            });
        }

        // Show explanation
        if (expBox) expBox.style.display = "block";
    });

    // Display score summary
    const scoreResult = document.getElementById("quizScoreResult");
    const percent = Math.round((score / activeQuizData.length) * 100);
    let gradeMsg = "Great job! Keep practicing.";
    if (percent === 100) gradeMsg = "🌟 Perfect score! Outstanding mastery.";
    else if (percent >= 80) gradeMsg = "👏 Great effort! Solid grasp of the concept.";
    else if (percent <= 40) gradeMsg = "💡 Don't worry, review the explanations above and try again!";

    scoreResult.innerHTML = `
        <h3>Your Score: ${score} / ${activeQuizData.length} (${percent}%)</h3>
        <p>${gradeMsg}</p>
    `;
    scoreResult.style.display = "block";

    // Show reset button
    const resetBtn = document.getElementById("resetQuizBtn");
    resetBtn.style.display = "inline-block";
    resetBtn.onclick = () => {
        document.getElementById("quizTopic").focus();
        document.getElementById("quizTopic").select();
    };

    // Scroll to results
    scoreResult.scrollIntoView({ behavior: "smooth" });
}

// Utility: Button loading state
function setLoading(btn, isLoading) {
    const textSpan = btn.querySelector(".btn-text");
    const spinner = btn.querySelector(".spinner");

    if (isLoading) {
        btn.disabled = true;
        if (textSpan) textSpan.dataset.originalText = textSpan.textContent;
        if (textSpan) textSpan.textContent = "Processing...";
        if (spinner) spinner.style.display = "inline-block";
    } else {
        btn.disabled = false;
        if (textSpan && textSpan.dataset.originalText) {
            textSpan.textContent = textSpan.dataset.originalText;
        }
        if (spinner) spinner.style.display = "none";
    }
}

// Utility: Copy to clipboard
function copyToClipboard(elementId) {
    const el = document.getElementById(elementId);
    if (!el) return;
    const text = el.textContent;
    navigator.clipboard.writeText(text).then(() => {
        alert("Copied to clipboard! 📋");
    }).catch(() => {
        alert("Failed to copy text.");
    });
}

// Utility: Escape HTML
function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}
