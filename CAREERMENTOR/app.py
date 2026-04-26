"""
Explainable AI-Driven Career Mentorship System
Flask Backend — Main Application
"""

from flask import Flask, render_template, request, jsonify
import json, os, sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "career_mentor_secret_2024"

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DATA_DIR    = os.path.join(BASE_DIR, "data")
CAREERS_FILE = os.path.join(DATA_DIR, "careers.json")
DB_FILE     = os.path.join(DATA_DIR, "mentorship.db")


# ── Database ──────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS user_sessions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, skills TEXT, target_career TEXT,
        missing_skills TEXT, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS fresher_sessions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, education TEXT, interests TEXT,
        subjects TEXT, recommended_careers TEXT, created_at TEXT)""")
    conn.commit(); conn.close()

def save_session(name, skills, career, missing):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT INTO user_sessions VALUES(NULL,?,?,?,?,?)",
        (name, json.dumps(skills), career,
         json.dumps(missing), datetime.now().isoformat()))
    conn.commit(); conn.close()

def save_fresher(name, edu, interests, subjects, recs):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT INTO fresher_sessions VALUES(NULL,?,?,?,?,?,?)",
        (name, edu, json.dumps(interests), json.dumps(subjects),
         json.dumps([r["career"] for r in recs]), datetime.now().isoformat()))
    conn.commit(); conn.close()


# ── Career Data ───────────────────────────────────────────
def load_careers():
    with open(CAREERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# ── Core AI Logic ─────────────────────────────────────────
def normalize(skill):
    return skill.strip().lower()

def analyze_skill_gap(user_skills, career_data):
    required = career_data["required_skills"]
    present, mc, mi, ma = [], [], [], []

    for name, info in required.items():
        sn = normalize(name)
        found = any(
            sn in normalize(us) or normalize(us) in sn
            for us in user_skills
        )
        if found:
            present.append(name)
        else:
            entry = {
                "name": name,
                "priority": info["priority"],
                "reason": info["reason"],
                "resources": info["resources"],
                "estimated_weeks": info["estimated_weeks"]
            }
            if info["priority"] == "critical":   mc.append(entry)
            elif info["priority"] == "important": mi.append(entry)
            else:                                 ma.append(entry)

    missing = mc + mi + ma
    total   = len(required)
    score   = round(len(present) / total * 100) if total else 0
    readiness = ("Job-Ready" if score >= 80 else
                 "Intermediate" if score >= 50 else
                 "Developing"   if score >= 25 else "Beginner")
    color = ("green"  if score >= 80 else
             "orange" if score >= 50 else
             "yellow" if score >= 25 else "red")

    return {
        "present_skills":  present,
        "missing_skills":  missing,
        "match_score":     score,
        "readiness_level": readiness,
        "readiness_color": color,
        "roadmap":         generate_roadmap(missing),
        "total_weeks":     sum(s["estimated_weeks"] for s in missing),
    }

def generate_roadmap(missing):
    roadmap, step = [], 1
    phases = [
        ("critical",  "Phase 1 - Foundations",      "foundational prerequisite"),
        ("important", "Phase 2 - Core Skills",       "core competency"),
        ("advanced",  "Phase 3 - Advanced Mastery",  "specialized advanced skill"),
    ]
    for key, label, desc in phases:
        for skill in [s for s in missing if s["priority"] == key]:
            roadmap.append({
                "step": step, "phase": label, "phase_key": key,
                "skill": skill["name"], "reason": skill["reason"],
                "resources": skill["resources"],
                "estimated_weeks": skill["estimated_weeks"],
                "xai_explanation": (
                    f"Step {step} places '{skill['name']}' here because "
                    f"it is a {desc} for this career path."
                ),
            })
            step += 1
    return roadmap


# ── Fresher Recommendation Engine ─────────────────────────
FRESHER_RULES = [
    {"interests": ["Web Development"], "subjects": ["Programming"],
     "careers": ["Frontend Developer", "Web Developer", "Full Stack Developer"],
     "reason": "Your interest in Web Development combined with Programming is the ideal starting point for frontend and full-stack roles."},
    {"interests": ["Web Development", "Problem Solving"], "subjects": ["Programming", "Mathematics"],
     "careers": ["Backend Developer", "Full Stack Developer", "Software Developer"],
     "reason": "Combining Web Development with Problem Solving and Mathematics maps directly to backend and software development."},
    {"interests": ["AI/ML"], "subjects": ["Mathematics", "Programming"],
     "careers": ["AI Engineer", "Machine Learning Engineer", "Data Scientist"],
     "reason": "AI/ML interest paired with Mathematics and Programming is the classic foundation for AI engineering roles."},
    {"interests": ["AI/ML", "Data Analysis"], "subjects": ["Mathematics", "Statistics"],
     "careers": ["Data Scientist", "Machine Learning Engineer", "NLP Engineer"],
     "reason": "AI/ML and Data Analysis with Mathematics/Statistics aligns perfectly with Data Science paths."},
    {"interests": ["Data Analysis"], "subjects": ["Statistics", "Mathematics"],
     "careers": ["Data Scientist", "Database Developer", "Machine Learning Engineer"],
     "reason": "Data Analysis interest with Statistics and Mathematics points directly to data-focused careers."},
    {"interests": ["UI Design"], "subjects": ["Design", "Programming"],
     "careers": ["Frontend Developer", "Mobile App Developer", "Web Developer"],
     "reason": "UI Design with Programming is the ideal combination for frontend and mobile roles."},
    {"interests": ["UI Design"], "subjects": ["Design"],
     "careers": ["Frontend Developer", "AR/VR Developer", "Mobile App Developer"],
     "reason": "A strong Design background with UI interest aligns with visual and experience-focused roles."},
    {"interests": ["Problem Solving"], "subjects": ["Mathematics", "Programming"],
     "careers": ["Software Engineer", "Software Developer", "Backend Developer"],
     "reason": "Problem Solving with Mathematics and Programming is the core profile for software engineering."},
    {"interests": ["Problem Solving", "AI/ML"], "subjects": ["Programming", "Statistics"],
     "careers": ["AI Engineer", "Software Engineer", "Computer Vision Engineer"],
     "reason": "Problem Solving with AI/ML and Programming/Statistics maps to AI and advanced software roles."},
    {"interests": ["Data Analysis", "Problem Solving"], "subjects": ["Statistics", "Programming"],
     "careers": ["Data Scientist", "Backend Developer", "Database Developer"],
     "reason": "Analytical interest with programming is a natural fit for data science and backend engineering."},
]

def recommend_for_fresher(interests, subjects):
    careers_data = load_careers()
    scored = {}
    for rule in FRESHER_RULES:
        i_overlap = len(set(rule["interests"]) & set(interests))
        s_overlap  = len(set(rule["subjects"])  & set(subjects))
        score = (i_overlap * 2) + s_overlap
        if score > 0:
            for career in rule["careers"]:
                if career in careers_data:
                    if career not in scored or scored[career]["score"] < score:
                        scored[career] = {
                            "career": career, "score": score,
                            "reason": rule["reason"],
                            "icon": careers_data[career]["icon"],
                            "description": careers_data[career]["description"],
                        }
    top = sorted(scored.values(), key=lambda x: x["score"], reverse=True)[:3]
    if not top:
        fb = "Software Developer"
        top = [{"career": fb, "score": 0,
                "reason": "Software Development is a great starting point for any tech career.",
                "icon": careers_data[fb]["icon"],
                "description": careers_data[fb]["description"]}]

    results = []
    for item in top:
        cd       = careers_data[item["career"]]
        analysis = analyze_skill_gap([], cd)
        max_score = max(1, (len(interests) * 2) + len(subjects))
        pct = min(100, round((item["score"] / max_score) * 100))
        results.append({
            "career":        item["career"],
            "icon":          item["icon"],
            "description":   item["description"],
            "match_reason":  item["reason"],
            "match_pct":     pct,
            "roadmap":       analysis["roadmap"],
            "missing_skills": analysis["missing_skills"],
            "total_weeks":   analysis["total_weeks"],
        })
    return results


# ── Routes ────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/fresher")
def fresher():
    return render_template("fresher.html")

@app.route("/experienced")
def experienced():
    careers = load_careers()
    career_list = [{"name": n, "icon": d["icon"], "description": d["description"]}
                   for n, d in careers.items()]
    return render_template("experienced.html", careers=career_list)

@app.route("/recommend", methods=["POST"])
def recommend():
    data      = request.get_json()
    name      = data.get("name", "").strip()
    education = data.get("education", "").strip()
    interests = data.get("interests", [])
    subjects  = data.get("subjects", [])
    if not name or not education:
        return jsonify({"error": "Name and education are required."}), 400
    recs = recommend_for_fresher(interests, subjects)
    save_fresher(name, education, interests, subjects, recs)
    return jsonify({"name": name, "education": education,
                    "interests": interests, "subjects": subjects,
                    "recommendations": recs})

@app.route("/analyze", methods=["POST"])
def analyze():
    data   = request.get_json()
    name   = data.get("name", "").strip()
    raw    = data.get("skills", "")
    career = data.get("career", "")
    if not name or not raw or not career:
        return jsonify({"error": "All fields are required."}), 400
    user_skills = [s.strip() for s in raw.replace("\n", ",").split(",") if s.strip()]
    careers = load_careers()
    if career not in careers:
        return jsonify({"error": "Invalid career selected."}), 400
    cd     = careers[career]
    result = analyze_skill_gap(user_skills, cd)
    save_session(name, user_skills, career, result["missing_skills"])
    return jsonify({"name": name, "career": career,
                    "career_icon": cd["icon"],
                    "career_description": cd["description"],
                    "user_skills": user_skills, **result})

@app.route("/careers")
def careers():
    d = load_careers()
    return jsonify([{"name": n, "icon": v["icon"], "description": v["description"]}
                    for n, v in d.items()])


# ── Run ───────────────────────────────────────────────────
import os as _os
init_db()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0",
            port=int(_os.environ.get("PORT", 5000)))