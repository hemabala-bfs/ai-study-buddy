// ===================================================================
// AI Study Buddy V2.0 - Dashboard Controller
// ===================================================================
// Manages all dashboard interactions: analytics, charts, quizzes,
// study plans, resource search, and model info.
// ===================================================================

// --------------- Global Chart Defaults ---------------
Chart.defaults.font.family = "'Plus Jakarta Sans', sans-serif";
Chart.defaults.font.size = 13;
Chart.defaults.color = "#64748b";

// --------------- Color Palette ---------------
const COLORS = {
    primary: "#6366f1",
    primaryLight: "#818cf8",
    primaryDark: "#4f46e5",
    success: "#22c55e",
    successLight: "#86efac",
    danger: "#ef4444",
    dangerLight: "#fca5a5",
    warning: "#f59e0b",
    warningLight: "#fcd34d",
    info: "#3b82f6",
    infoLight: "#93c5fd",
    purple: "#a855f7",
    pink: "#ec4899",
    teal: "#14b8a6",
    orange: "#f97316",
    slate: "#94a3b8",
    chartPalette: [
        "#6366f1", "#22c55e", "#f59e0b", "#ef4444",
        "#3b82f6", "#a855f7", "#ec4899", "#14b8a6",
        "#f97316", "#64748b"
    ],
};

// --------------- Active Chart Instances ---------------
let topicChartInstance = null;
let progressChartInstance = null;
let activityChartInstance = null;

// ===================================================================
// Entry Point
// ===================================================================
document.addEventListener("DOMContentLoaded", () => {
    checkApiStatus();
    loadAnalytics();
    initNavigation();
    initResourceSearch();
    initStudyPlan();
    initAdaptiveQuiz();
    initModelInfo();
    initMobileMenu();
});

// ===================================================================
// 1. API Status Check
// ===================================================================
async function checkApiStatus() {
    const pill = document.getElementById("api-status-pill");
    if (!pill) return;

    pill.textContent = "Connecting…";
    pill.className = "status-pill status-connecting";

    try {
        const res = await fetch("/api/status");
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        if (data.status === "online" || data.status === "ok") {
            pill.textContent = `Online — v${data.version || "2.0"}`;
            pill.className = "status-pill status-online";
        } else {
            pill.textContent = "Degraded";
            pill.className = "status-pill status-degraded";
        }

        // Update secondary status indicators if present
        const sdkBadge = document.getElementById("sdk-mode-badge");
        if (sdkBadge && data.sdk_mode) {
            sdkBadge.textContent = data.sdk_mode;
        }
        const mlBadge = document.getElementById("ml-engine-badge");
        if (mlBadge && data.ml_engine) {
            mlBadge.textContent = data.ml_engine;
        }
    } catch (err) {
        pill.textContent = "Offline";
        pill.className = "status-pill status-offline";
        console.error("Status check failed:", err);
    }
}

// ===================================================================
// 2. Load Analytics
// ===================================================================
async function loadAnalytics() {
    const statsSection = document.getElementById("stats-section");
    if (statsSection) setLoading(statsSection, true);

    try {
        const res = await fetch("/api/analytics");
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        // --- Stat Cards ---
        const stats = data.stats || {};
        animateNumber(document.getElementById("stat-quizzes"), stats.total_quizzes || 0, 1200);
        animateNumber(document.getElementById("stat-hours"), stats.study_hours || 0, 1200, 1);
        animateNumber(document.getElementById("stat-streak"), data.learning_streak || stats.streak || 0, 1000);
        animateNumber(document.getElementById("stat-avg-score"), stats.avg_score || 0, 1400, 1, "%");

        // --- Charts ---
        initTopicChart(data.topic_performance || []);
        initProgressChart(data.weekly_progress || []);
        initActivityChart(data.feature_usage || {});

        // --- Strengths ---
        renderBadgeList(
            document.getElementById("strengths-list"),
            data.strengths || [],
            "badge-success"
        );

        // --- Weaknesses ---
        renderBadgeList(
            document.getElementById("weaknesses-list"),
            data.weaknesses || [],
            "badge-danger"
        );

        // --- Recent Activity ---
        renderRecentActivity(data.recent_activity || []);
    } catch (err) {
        console.error("Failed to load analytics:", err);
        showEmptyState(
            document.getElementById("stats-section"),
            "Could not load analytics. Please check the API connection."
        );
    } finally {
        if (statsSection) setLoading(statsSection, false);
    }
}

// ===================================================================
// 3. Topic Performance Chart (Horizontal Bar)
// ===================================================================
function initTopicChart(topicData) {
    const canvas = document.getElementById("topicChart");
    if (!canvas) return;

    if (!topicData || topicData.length === 0) {
        showEmptyState(canvas.parentElement, "No topic data yet. Take a quiz to see your performance!");
        canvas.style.display = "none";
        return;
    }
    canvas.style.display = "";

    const labels = topicData.map((t) => t.topic || t.name || "Unknown");
    const scores = topicData.map((t) => t.avg_score ?? t.score ?? 0);
    const attempts = topicData.map((t) => t.attempts ?? t.count ?? 0);
    const bgColors = scores.map((s) => (s >= 70 ? COLORS.success : COLORS.danger));
    const borderColors = scores.map((s) =>
        s >= 70 ? COLORS.success : COLORS.danger
    );

    if (topicChartInstance) topicChartInstance.destroy();

    topicChartInstance = new Chart(canvas, {
        type: "bar",
        data: {
            labels,
            datasets: [
                {
                    label: "Avg Score",
                    data: scores,
                    backgroundColor: bgColors.map((c) => c + "cc"),
                    borderColor: borderColors,
                    borderWidth: 2,
                    borderRadius: 6,
                    borderSkipped: false,
                },
            ],
        },
        options: {
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label(ctx) {
                            const idx = ctx.dataIndex;
                            return `Score: ${ctx.parsed.x}%  •  Attempts: ${attempts[idx]}`;
                        },
                    },
                },
            },
            scales: {
                x: {
                    beginAtZero: true,
                    max: 100,
                    grid: { color: "rgba(100,116,139,0.1)" },
                    ticks: { callback: (v) => v + "%" },
                },
                y: {
                    grid: { display: false },
                    ticks: {
                        font: { weight: "600" },
                    },
                },
            },
        },
    });
}

// ===================================================================
// 4. Weekly Progress Chart (Line)
// ===================================================================
function initProgressChart(weeklyData) {
    const canvas = document.getElementById("progressChart");
    if (!canvas) return;

    if (!weeklyData || weeklyData.length === 0) {
        showEmptyState(canvas.parentElement, "No progress data yet. Keep studying to track your improvement!");
        canvas.style.display = "none";
        return;
    }
    canvas.style.display = "";

    const labels = weeklyData.map((w) => formatDate(w.date || w.week || ""));
    const scores = weeklyData.map((w) => w.avg_score ?? w.score ?? 0);

    if (progressChartInstance) progressChartInstance.destroy();

    progressChartInstance = new Chart(canvas, {
        type: "line",
        data: {
            labels,
            datasets: [
                {
                    label: "Avg Score",
                    data: scores,
                    borderColor: COLORS.primary,
                    backgroundColor: (ctx) => {
                        const chart = ctx.chart;
                        const { ctx: c, chartArea } = chart;
                        if (!chartArea) return COLORS.primary + "22";
                        const gradient = c.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
                        gradient.addColorStop(0, COLORS.primary + "44");
                        gradient.addColorStop(1, COLORS.primary + "05");
                        return gradient;
                    },
                    fill: true,
                    tension: 0.4,
                    borderWidth: 3,
                    pointBackgroundColor: "#fff",
                    pointBorderColor: COLORS.primary,
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 7,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label(ctx) {
                            return `Score: ${ctx.parsed.y}%`;
                        },
                    },
                },
            },
            scales: {
                x: {
                    grid: { color: "rgba(100,116,139,0.08)" },
                },
                y: {
                    beginAtZero: true,
                    max: 100,
                    grid: { color: "rgba(100,116,139,0.1)" },
                    ticks: { callback: (v) => v + "%" },
                },
            },
        },
    });
}

// ===================================================================
// 5. Feature Usage Chart (Doughnut)
// ===================================================================
function initActivityChart(featureData) {
    const canvas = document.getElementById("activityChart");
    if (!canvas) return;

    const entries = Object.entries(featureData || {});
    if (entries.length === 0) {
        showEmptyState(canvas.parentElement, "No activity data yet. Explore quizzes, resources, and study plans!");
        canvas.style.display = "none";
        return;
    }
    canvas.style.display = "";

    const labels = entries.map(([k]) => k);
    const values = entries.map(([, v]) => v);

    if (activityChartInstance) activityChartInstance.destroy();

    activityChartInstance = new Chart(canvas, {
        type: "doughnut",
        data: {
            labels,
            datasets: [
                {
                    data: values,
                    backgroundColor: COLORS.chartPalette.slice(0, labels.length),
                    borderColor: "#fff",
                    borderWidth: 3,
                    hoverOffset: 8,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: "65%",
            plugins: {
                legend: {
                    position: "bottom",
                    labels: {
                        padding: 16,
                        usePointStyle: true,
                        pointStyle: "circle",
                    },
                },
                tooltip: {
                    callbacks: {
                        label(ctx) {
                            const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                            const pct = total ? ((ctx.parsed / total) * 100).toFixed(1) : 0;
                            return `${ctx.label}: ${ctx.parsed} (${pct}%)`;
                        },
                    },
                },
            },
        },
    });
}

// ===================================================================
// 6. Navigation
// ===================================================================
function initNavigation() {
    document.querySelectorAll('a[href^="#"]').forEach((link) => {
        link.addEventListener("click", (e) => {
            const targetId = link.getAttribute("href").slice(1);
            const target = document.getElementById(targetId);
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: "smooth", block: "start" });
                // Close mobile menu if open
                const navLinks = document.querySelector(".nav-links");
                if (navLinks) navLinks.classList.remove("active");
            }
        });
    });
}

// ===================================================================
// 7. Resource Search
// ===================================================================
function initResourceSearch() {
    const searchInput = document.getElementById("resourceSearchInput");
    const searchBtn = document.getElementById("resourceSearchBtn");
    const categoryFilter = document.getElementById("resourceCategoryFilter");
    const difficultyFilter = document.getElementById("resourceDifficultyFilter");
    const resultsContainer = document.getElementById("resourceResults");

    if (!searchInput || !resultsContainer) return;

    async function doSearch() {
        const query = searchInput.value.trim();
        const category = categoryFilter ? categoryFilter.value : "";
        const difficulty = difficultyFilter ? difficultyFilter.value : "";

        if (!query && !category && !difficulty) return;

        setLoading(resultsContainer, true);

        try {
            let data;
            if (query && !category && !difficulty) {
                // Use recommendations endpoint for simple topic search
                const res = await fetch(
                    `/api/recommendations?topic=${encodeURIComponent(query)}&n=8`
                );
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                data = await res.json();
                renderResourceCards(data.recommendations || [], resultsContainer);
            } else {
                // Use full resource search with filters
                const params = new URLSearchParams();
                if (query) params.set("q", query);
                if (category) params.set("category", category);
                if (difficulty) params.set("difficulty", difficulty);

                const res = await fetch(`/api/resources/search?${params}`);
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                data = await res.json();
                renderResourceCards(data.resources || [], resultsContainer);
            }
        } catch (err) {
            console.error("Resource search failed:", err);
            showEmptyState(resultsContainer, "Search failed. Please try again.");
        } finally {
            setLoading(resultsContainer, false);
        }
    }

    if (searchBtn) searchBtn.addEventListener("click", doSearch);
    searchInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") doSearch();
    });
    if (categoryFilter) categoryFilter.addEventListener("change", doSearch);
    if (difficultyFilter) difficultyFilter.addEventListener("change", doSearch);
}

function renderResourceCards(resources, container) {
    if (!container) return;

    if (!resources || resources.length === 0) {
        showEmptyState(container, "No resources found. Try a different search term.");
        return;
    }

    const difficultyColors = {
        easy: COLORS.success,
        medium: COLORS.warning,
        hard: COLORS.danger,
    };
    const categoryColors = {
        video: COLORS.info,
        article: COLORS.purple,
        tutorial: COLORS.teal,
        exercise: COLORS.orange,
        course: COLORS.pink,
        documentation: COLORS.primaryLight,
    };

    container.innerHTML = resources
        .map((r) => {
            const diff = (r.difficulty || "medium").toLowerCase();
            const cat = (r.category || r.type || "article").toLowerCase();
            const similarity = r.similarity_score ?? r.score ?? 0;
            const widthPct = Math.min(Math.round(similarity * 100), 100);
            const catColor = categoryColors[cat] || COLORS.slate;
            const diffColor = difficultyColors[diff] || COLORS.warning;

            return `
                <div class="resource-card">
                    <div class="resource-card-header">
                        <h4 class="resource-title">${escapeHtml(r.title || "Untitled")}</h4>
                        <div class="resource-badges">
                            <span class="badge" style="background:${catColor}22;color:${catColor};border:1px solid ${catColor}44">
                                ${escapeHtml(cat)}
                            </span>
                            <span class="badge" style="background:${diffColor}22;color:${diffColor};border:1px solid ${diffColor}44">
                                ${escapeHtml(diff)}
                            </span>
                        </div>
                    </div>
                    ${r.description ? `<p class="resource-desc">${escapeHtml(r.description)}</p>` : ""}
                    <div class="resource-meta">
                        <div class="similarity-bar-container">
                            <span class="similarity-label">Relevance</span>
                            <div class="similarity-bar">
                                <div class="similarity-fill" style="width:${widthPct}%;background:${COLORS.primary}"></div>
                            </div>
                            <span class="similarity-value">${widthPct}%</span>
                        </div>
                        ${r.estimated_minutes ? `<span class="resource-time">⏱ ${r.estimated_minutes} min</span>` : ""}
                        ${r.type ? `<span class="resource-type">${escapeHtml(r.type)}</span>` : ""}
                    </div>
                </div>
            `;
        })
        .join("");
}

// ===================================================================
// 8. Study Plan Generator
// ===================================================================
function initStudyPlan() {
    const btn = document.getElementById("generatePlanBtn");
    const content = document.getElementById("studyPlanContent");

    if (!btn || !content) return;

    btn.addEventListener("click", async () => {
        setLoading(content, true);
        btn.disabled = true;
        btn.textContent = "Generating…";

        try {
            const res = await fetch("/api/study-plan", { method: "POST" });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            renderStudyPlan(data.plan || [], content);
        } catch (err) {
            console.error("Study plan generation failed:", err);
            showEmptyState(content, "Could not generate study plan. Please try again.");
        } finally {
            btn.disabled = false;
            btn.textContent = "Generate Study Plan";
            setLoading(content, false);
        }
    });
}

function renderStudyPlan(plan, container) {
    if (!container) return;

    if (!plan || plan.length === 0) {
        showEmptyState(container, "No study plan data available. Take some quizzes first!");
        return;
    }

    const priorityColors = {
        high: COLORS.danger,
        medium: COLORS.warning,
        low: COLORS.success,
    };

    container.innerHTML = plan
        .map((item, idx) => {
            const pColor = priorityColors[(item.priority || "medium").toLowerCase()] || COLORS.warning;
            const resources = item.resources || [];

            return `
                <div class="plan-card" style="animation-delay:${idx * 0.08}s">
                    <div class="plan-card-header">
                        <div class="plan-day">
                            <span class="plan-day-label">Day</span>
                            <span class="plan-day-number">${item.day || idx + 1}</span>
                        </div>
                        <div class="plan-info">
                            <h4 class="plan-topic">${escapeHtml(item.topic || "General Review")}</h4>
                            <span class="badge" style="background:${pColor}22;color:${pColor};border:1px solid ${pColor}44">
                                ${escapeHtml((item.priority || "medium").toUpperCase())} PRIORITY
                            </span>
                        </div>
                    </div>
                    <div class="plan-card-body">
                        <div class="plan-scores">
                            <span class="score-current">${item.current_score ?? "—"}%</span>
                            <span class="score-arrow">→</span>
                            <span class="score-target">${item.target_score ?? "—"}%</span>
                        </div>
                        <p class="plan-action">${escapeHtml(item.action || "Review and practice")}</p>
                        ${item.estimated_minutes ? `<span class="plan-time">⏱ ${item.estimated_minutes} min</span>` : ""}
                    </div>
                    ${
                        resources.length > 0
                            ? `<div class="plan-resources">
                                <h5>Resources:</h5>
                                <ul>${resources.map((r) => `<li>${escapeHtml(typeof r === "string" ? r : r.title || r)}</li>`).join("")}</ul>
                               </div>`
                            : ""
                    }
                </div>
            `;
        })
        .join("");
}

// ===================================================================
// 9. Adaptive Quiz
// ===================================================================
function initAdaptiveQuiz() {
    const startBtn = document.getElementById("startAdaptiveQuizBtn");
    const submitBtn = document.getElementById("submitAdaptiveQuizBtn");
    const topicInput = document.getElementById("adaptiveQuizTopic");
    const quizContainer = document.getElementById("adaptiveQuizContent");
    const resultsContainer = document.getElementById("adaptiveQuizResults");
    const difficultyBadge = document.getElementById("quizDifficultyBadge");

    let currentQuiz = null;

    if (!startBtn || !quizContainer) return;

    // Load quiz history on startup
    loadQuizHistory();

    // --- Start Quiz ---
    startBtn.addEventListener("click", async () => {
        const topic = topicInput ? topicInput.value.trim() : "";
        if (!topic) {
            topicInput.focus();
            topicInput.classList.add("input-error");
            setTimeout(() => topicInput.classList.remove("input-error"), 1500);
            return;
        }

        setLoading(quizContainer, true);
        startBtn.disabled = true;
        startBtn.textContent = "Loading Quiz…";
        if (resultsContainer) resultsContainer.innerHTML = "";

        try {
            const res = await fetch("/api/quiz/adaptive", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ topic, user_id: "default" }),
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            currentQuiz = data;

            // Show difficulty badge
            if (difficultyBadge) {
                const diff = (data.difficulty || "medium").toLowerCase();
                const diffColors = { easy: COLORS.success, medium: COLORS.warning, hard: COLORS.danger };
                const color = diffColors[diff] || COLORS.warning;
                difficultyBadge.textContent = diff.toUpperCase();
                difficultyBadge.style.background = color + "22";
                difficultyBadge.style.color = color;
                difficultyBadge.style.border = `1px solid ${color}44`;
                difficultyBadge.style.display = "inline-block";
            }

            renderAdaptiveQuiz(data, quizContainer);
        } catch (err) {
            console.error("Failed to load adaptive quiz:", err);
            showEmptyState(quizContainer, "Could not load quiz. Please try again.");
        } finally {
            startBtn.disabled = false;
            startBtn.textContent = "Start Quiz";
            setLoading(quizContainer, false);
        }
    });

    // --- Submit Quiz ---
    if (submitBtn) {
        submitBtn.addEventListener("click", async () => {
            if (!currentQuiz || !currentQuiz.quiz) return;

            const questions = currentQuiz.quiz;
            let score = 0;
            const total = questions.length;
            const answeredQuestions = [];

            questions.forEach((q, i) => {
                const selected = document.querySelector(
                    `input[name="adaptive-q${i}"]:checked`
                );
                const userAnswer = selected ? selected.value : null;
                const isCorrect =
                    userAnswer !== null &&
                    userAnswer === (q.correct_answer || q.answer || "").toString();

                if (isCorrect) score++;

                answeredQuestions.push({
                    question: q.question,
                    user_answer: userAnswer,
                    correct_answer: q.correct_answer || q.answer,
                    correct: isCorrect,
                });

                // Highlight answers
                const options = document.querySelectorAll(`input[name="adaptive-q${i}"]`);
                options.forEach((opt) => {
                    const label = opt.closest("label") || opt.parentElement;
                    opt.disabled = true;
                    if (opt.value === (q.correct_answer || q.answer || "").toString()) {
                        label.classList.add("quiz-correct");
                    } else if (opt.checked && !isCorrect) {
                        label.classList.add("quiz-incorrect");
                    }
                });
            });

            submitBtn.disabled = true;
            submitBtn.textContent = "Submitting…";

            try {
                const res = await fetch("/api/quiz/submit", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        topic: currentQuiz.topic || "General",
                        score,
                        total,
                        difficulty: currentQuiz.difficulty || "medium",
                        questions: answeredQuestions,
                    }),
                });
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                const result = await res.json();
                renderQuizResults(result, score, total, resultsContainer);
                loadQuizHistory();

                // Track session
                fetch("/api/session/track", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        topic: currentQuiz.topic || "General",
                        feature_used: "adaptive_quiz",
                        duration: 0,
                    }),
                }).catch(() => {});
            } catch (err) {
                console.error("Failed to submit quiz:", err);
                // Show local results even if submission fails
                if (resultsContainer) {
                    resultsContainer.innerHTML = `
                        <div class="quiz-results-card">
                            <h3>Your Score: ${score}/${total} (${Math.round((score / total) * 100)}%)</h3>
                            <p class="text-muted">Could not save results to server.</p>
                        </div>
                    `;
                }
            } finally {
                submitBtn.style.display = "none";
            }
        });
    }
}

function renderAdaptiveQuiz(data, container) {
    if (!container) return;
    const questions = data.quiz || [];

    if (questions.length === 0) {
        showEmptyState(container, "No questions available for this topic. Try another topic!");
        return;
    }

    const submitBtn = document.getElementById("submitAdaptiveQuizBtn");

    container.innerHTML = questions
        .map((q, i) => {
            const options = q.options || q.choices || [];
            return `
                <div class="quiz-question-card" style="animation-delay:${i * 0.06}s">
                    <div class="quiz-question-number">Q${i + 1}</div>
                    <p class="quiz-question-text">${escapeHtml(q.question)}</p>
                    <div class="quiz-options">
                        ${options
                            .map(
                                (opt, j) => `
                                <label class="quiz-option">
                                    <input type="radio" name="adaptive-q${i}" value="${escapeHtml(typeof opt === "string" ? opt : opt.text || opt)}" />
                                    <span class="quiz-option-text">${escapeHtml(typeof opt === "string" ? opt : opt.text || opt)}</span>
                                </label>
                            `
                            )
                            .join("")}
                    </div>
                </div>
            `;
        })
        .join("");

    if (submitBtn) {
        submitBtn.style.display = "inline-flex";
        submitBtn.disabled = false;
        submitBtn.textContent = "Submit Answers";
    }
}

function renderQuizResults(response, score, total, container) {
    if (!container) return;

    const pct = total > 0 ? Math.round((score / total) * 100) : 0;
    const adaptiveScore = response.adaptive_score ?? pct;
    const mastery = response.mastery || "beginner";
    const nextDiff = response.next_difficulty || "medium";

    const masteryColors = {
        beginner: COLORS.info,
        intermediate: COLORS.warning,
        advanced: COLORS.success,
        expert: COLORS.purple,
    };
    const mColor = masteryColors[mastery.toLowerCase()] || COLORS.info;

    let emoji = "🎯";
    let message = "Good effort!";
    if (pct >= 90) { emoji = "🏆"; message = "Outstanding performance!"; }
    else if (pct >= 70) { emoji = "🌟"; message = "Great job! Keep it up!"; }
    else if (pct >= 50) { emoji = "💪"; message = "Getting there! Keep practicing."; }
    else { emoji = "📚"; message = "Review this topic and try again!"; }

    container.innerHTML = `
        <div class="quiz-results-card">
            <div class="quiz-results-emoji">${emoji}</div>
            <h3 class="quiz-results-score">${score} / ${total}</h3>
            <p class="quiz-results-pct">${pct}%</p>
            <p class="quiz-results-message">${message}</p>
            <div class="quiz-results-meta">
                <div class="result-item">
                    <span class="result-label">Adaptive Score</span>
                    <span class="result-value">${typeof adaptiveScore === "number" ? adaptiveScore.toFixed(1) : adaptiveScore}</span>
                </div>
                <div class="result-item">
                    <span class="result-label">Mastery</span>
                    <span class="badge" style="background:${mColor}22;color:${mColor};border:1px solid ${mColor}44">${escapeHtml(mastery.toUpperCase())}</span>
                </div>
                <div class="result-item">
                    <span class="result-label">Next Difficulty</span>
                    <span class="result-value">${escapeHtml(nextDiff)}</span>
                </div>
            </div>
        </div>
    `;
}

async function loadQuizHistory() {
    const table = document.getElementById("quizHistoryTable");
    if (!table) return;

    try {
        const res = await fetch("/api/analytics");
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const activity = data.recent_activity || [];

        const quizActivity = activity.filter(
            (a) => a.type === "quiz" || a.feature === "quiz" || a.feature_used === "adaptive_quiz"
        );

        const tbody = table.querySelector("tbody") || table;

        if (quizActivity.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="empty-table-state">
                        🎓 Start your first quiz to build your history!
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = quizActivity
            .slice(0, 10)
            .map(
                (a) => `
                <tr>
                    <td>${escapeHtml(a.topic || "—")}</td>
                    <td>${a.score ?? "—"}</td>
                    <td>${escapeHtml(a.difficulty || "—")}</td>
                    <td>${formatDate(a.date || a.timestamp || "")}</td>
                    <td>${a.mastery ? escapeHtml(a.mastery) : "—"}</td>
                </tr>
            `
            )
            .join("");
    } catch (err) {
        console.error("Failed to load quiz history:", err);
    }
}

// ===================================================================
// 10. Model Info
// ===================================================================
function initModelInfo() {
    const btn = document.getElementById("showModelInfoBtn");
    const panel = document.getElementById("modelInfoPanel");

    if (!btn || !panel) return;

    btn.addEventListener("click", async () => {
        if (panel.classList.contains("active")) {
            panel.classList.remove("active");
            panel.innerHTML = "";
            btn.textContent = "Show Model Info";
            return;
        }

        setLoading(panel, true);
        btn.disabled = true;
        btn.textContent = "Loading…";

        try {
            const res = await fetch("/api/model-info");
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();

            const model = data.model || {};
            const evaluation = data.evaluation || {};

            panel.classList.add("active");
            panel.innerHTML = `
                <div class="model-info-grid">
                    <div class="model-section">
                        <h4>Model Metadata</h4>
                        <table class="info-table">
                            <tr><td>Type</td><td><strong>${escapeHtml(model.type || model.model_type || "N/A")}</strong></td></tr>
                            <tr><td>Algorithm</td><td>${escapeHtml(model.algorithm || "N/A")}</td></tr>
                            <tr><td>Features</td><td>${model.features_count || model.n_features || "N/A"}</td></tr>
                            <tr><td>Training Date</td><td>${formatDate(model.trained_at || model.last_trained || "")}</td></tr>
                            <tr><td>Version</td><td>${escapeHtml(model.version || "1.0")}</td></tr>
                        </table>
                    </div>
                    <div class="model-section">
                        <h4>Evaluation Metrics</h4>
                        <table class="info-table">
                            <tr><td>Precision@5</td><td><strong>${typeof evaluation.precision_at_5 === "number" ? evaluation.precision_at_5.toFixed(4) : evaluation.precision_at_5 || "N/A"}</strong></td></tr>
                            <tr><td>MRR</td><td><strong>${typeof evaluation.mrr === "number" ? evaluation.mrr.toFixed(4) : evaluation.mrr || "N/A"}</strong></td></tr>
                            <tr><td>NDCG</td><td>${typeof evaluation.ndcg === "number" ? evaluation.ndcg.toFixed(4) : evaluation.ndcg || "N/A"}</td></tr>
                            <tr><td>Coverage</td><td>${typeof evaluation.coverage === "number" ? (evaluation.coverage * 100).toFixed(1) + "%" : evaluation.coverage || "N/A"}</td></tr>
                        </table>
                    </div>
                </div>
                ${
                    evaluation.per_query
                        ? `
                    <div class="model-section">
                        <h4>Per-Query Results</h4>
                        <div class="per-query-grid">
                            ${Object.entries(evaluation.per_query)
                                .map(
                                    ([query, result]) => `
                                <div class="per-query-item">
                                    <span class="per-query-label">${escapeHtml(query)}</span>
                                    <span class="per-query-value">${typeof result === "number" ? result.toFixed(3) : escapeHtml(String(result))}</span>
                                </div>
                            `
                                )
                                .join("")}
                        </div>
                    </div>
                `
                        : ""
                }
            `;
        } catch (err) {
            console.error("Failed to load model info:", err);
            showEmptyState(panel, "Could not load model information.");
            panel.classList.add("active");
        } finally {
            btn.disabled = false;
            btn.textContent = "Hide Model Info";
            setLoading(panel, false);
        }
    });
}

// ===================================================================
// 11. Mobile Menu
// ===================================================================
function initMobileMenu() {
    const hamburger = document.getElementById("hamburgerBtn") || document.querySelector(".hamburger");
    const navLinks = document.querySelector(".nav-links");

    if (!hamburger || !navLinks) return;

    hamburger.addEventListener("click", () => {
        navLinks.classList.toggle("active");
        hamburger.classList.toggle("active");
        hamburger.setAttribute(
            "aria-expanded",
            navLinks.classList.contains("active").toString()
        );
    });

    // Close on outside click
    document.addEventListener("click", (e) => {
        if (
            navLinks.classList.contains("active") &&
            !navLinks.contains(e.target) &&
            !hamburger.contains(e.target)
        ) {
            navLinks.classList.remove("active");
            hamburger.classList.remove("active");
            hamburger.setAttribute("aria-expanded", "false");
        }
    });
}

// ===================================================================
// 12. Utility Functions
// ===================================================================

/**
 * Escape HTML entities to prevent XSS.
 */
function escapeHtml(str) {
    if (str === null || str === undefined) return "";
    const text = String(str);
    const div = document.createElement("div");
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
}

/**
 * Toggle a loading spinner overlay on an element.
 */
function setLoading(element, isLoading) {
    if (!element) return;

    if (isLoading) {
        // Don't add duplicate spinners
        if (element.querySelector(".loading-overlay")) return;
        const overlay = document.createElement("div");
        overlay.className = "loading-overlay";
        overlay.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner-ring"></div>
                <span>Loading…</span>
            </div>
        `;
        element.style.position = element.style.position || "relative";
        element.appendChild(overlay);
    } else {
        const overlay = element.querySelector(".loading-overlay");
        if (overlay) overlay.remove();
    }
}

/**
 * Animate a number counting up from 0 to target.
 */
function animateNumber(element, target, duration = 1200, decimals = 0, suffix = "") {
    if (!element) return;

    const start = 0;
    const startTime = performance.now();
    const numTarget = parseFloat(target) || 0;

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // Ease-out cubic
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = start + (numTarget - start) * eased;

        element.textContent = current.toFixed(decimals) + suffix;

        if (progress < 1) {
            requestAnimationFrame(update);
        } else {
            element.textContent = numTarget.toFixed(decimals) + suffix;
        }
    }

    requestAnimationFrame(update);
}

/**
 * Display an empty state message inside a container.
 */
function showEmptyState(container, message) {
    if (!container) return;
    container.innerHTML = `
        <div class="empty-state">
            <div class="empty-state-icon">📋</div>
            <p class="empty-state-text">${escapeHtml(message)}</p>
        </div>
    `;
}

/**
 * Format a date string for display.
 */
function formatDate(dateStr) {
    if (!dateStr) return "—";
    try {
        const date = new Date(dateStr);
        if (isNaN(date.getTime())) return escapeHtml(dateStr);

        const now = new Date();
        const diffMs = now - date;
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

        if (diffDays === 0) return "Today";
        if (diffDays === 1) return "Yesterday";
        if (diffDays < 7) return `${diffDays} days ago`;

        return date.toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
            year: date.getFullYear() !== now.getFullYear() ? "numeric" : undefined,
        });
    } catch {
        return escapeHtml(dateStr);
    }
}

// ===================================================================
// Helper: Render badge list (strengths/weaknesses)
// ===================================================================
function renderBadgeList(container, items, badgeClass) {
    if (!container) return;

    if (!items || items.length === 0) {
        container.innerHTML = `<span class="text-muted">No data yet</span>`;
        return;
    }

    container.innerHTML = items
        .map(
            (item) =>
                `<span class="badge ${badgeClass}">${escapeHtml(typeof item === "string" ? item : item.topic || item.name || item)}</span>`
        )
        .join(" ");
}

// ===================================================================
// Helper: Render recent activity list
// ===================================================================
function renderRecentActivity(activities) {
    const container = document.getElementById("recentActivityList");
    if (!container) return;

    if (!activities || activities.length === 0) {
        showEmptyState(container, "No recent activity. Start studying to see your activity here!");
        return;
    }

    const iconMap = {
        quiz: "📝",
        study: "📖",
        resource: "🔗",
        plan: "📅",
        search: "🔍",
        adaptive_quiz: "🎯",
    };

    container.innerHTML = activities
        .slice(0, 10)
        .map((a) => {
            const type = a.type || a.feature_used || a.feature || "study";
            const icon = iconMap[type] || "📌";
            return `
                <div class="activity-item">
                    <span class="activity-icon">${icon}</span>
                    <div class="activity-info">
                        <span class="activity-title">${escapeHtml(a.topic || a.title || "Activity")}</span>
                        <span class="activity-detail">${escapeHtml(a.description || type)}${a.score !== undefined ? ` — Score: ${a.score}` : ""}</span>
                    </div>
                    <span class="activity-time">${formatDate(a.date || a.timestamp || "")}</span>
                </div>
            `;
        })
        .join("");
}
