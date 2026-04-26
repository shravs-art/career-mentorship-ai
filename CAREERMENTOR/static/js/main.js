/* ═══════════════════════════════════════════════════════════
   CareerLens — Frontend JavaScript
   Handles: form input, API calls, dynamic results rendering
   ═══════════════════════════════════════════════════════════ */

// ── Skill Chip Preview ────────────────────────────────────────────────────────
const skillsInput = document.getElementById("userSkills");
const skillChips  = document.getElementById("skillChips");

skillsInput.addEventListener("input", () => {
  const raw    = skillsInput.value;
  const skills = raw.split(",").map(s => s.trim()).filter(Boolean);
  skillChips.innerHTML = "";
  skills.forEach(skill => {
    const chip = document.createElement("span");
    chip.className = "skill-chip";
    chip.textContent = skill;
    skillChips.appendChild(chip);
  });
});


// ── Form Submit ───────────────────────────────────────────────────────────────
const form      = document.getElementById("mentorForm");
const submitBtn = document.getElementById("submitBtn");

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const name   = document.getElementById("userName").value.trim();
  const skills = document.getElementById("userSkills").value.trim();
  const career = document.querySelector('input[name="career"]:checked')?.value;

  if (!name || !skills || !career) {
    showFormError("Please fill in all fields and select a career.");
    return;
  }

  // Loading state
  submitBtn.disabled = true;
  submitBtn.querySelector(".btn-text").hidden = true;
  submitBtn.querySelector(".btn-arrow").hidden = true;
  submitBtn.querySelector(".btn-loader").hidden = false;

  try {
    const res  = await fetch("/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, skills, career }),
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || "Analysis failed.");
    }

    renderResults(data);
  } catch (err) {
    showFormError(err.message);
  } finally {
    submitBtn.disabled = false;
    submitBtn.querySelector(".btn-text").hidden = false;
    submitBtn.querySelector(".btn-arrow").hidden = false;
    submitBtn.querySelector(".btn-loader").hidden = true;
  }
});


// ── Error Display ─────────────────────────────────────────────────────────────
function showFormError(msg) {
  let err = document.getElementById("formError");
  if (!err) {
    err = document.createElement("div");
    err.id = "formError";
    err.style.cssText = `
      padding: 14px 20px;
      background: rgba(255,107,107,0.08);
      border: 1px solid rgba(255,107,107,0.25);
      border-radius: 6px;
      color: #ff6b6b;
      font-size: 14px;
      font-family: var(--font-mono);
    `;
    form.prepend(err);
  }
  err.textContent = `⚠ ${msg}`;
  setTimeout(() => err.remove(), 4000);
}


// ── Results Renderer ──────────────────────────────────────────────────────────
function renderResults(data) {
  const section   = document.getElementById("resultsSection");
  const container = document.getElementById("resultsContainer");

  const readinessColor = data.readiness_color;

  // ── HTML Assembly ──
  container.innerHTML = `

    <!-- Header -->
    <div class="results-header results-animate">
      <div>
        <div class="results-greeting">Analysis complete for</div>
        <h2 class="results-title">${escHtml(data.name)}</h2>
      </div>
      <div class="career-badge">
        <span class="career-badge-icon">${escHtml(data.career_icon)}</span>
        <span class="career-badge-name">${escHtml(data.career)}</span>
      </div>
    </div>

    <!-- Score Cards -->
    <div class="score-panel results-animate">
      <div class="score-card">
        <div class="score-card-label">Match Score</div>
        <div class="score-card-value ${readinessColor}">${data.match_score}%</div>
        <div class="score-card-sub">of required skills</div>
      </div>
      <div class="score-card">
        <div class="score-card-label">Readiness</div>
        <div class="score-card-value ${readinessColor}">${escHtml(data.readiness_level)}</div>
        <div class="score-card-sub">current level</div>
      </div>
      <div class="score-card">
        <div class="score-card-label">Est. Learning Time</div>
        <div class="score-card-value accent">${data.total_weeks}</div>
        <div class="score-card-sub">weeks to job-ready</div>
      </div>
    </div>

    <!-- Progress Bar -->
    <div class="progress-bar-wrap results-animate">
      <div class="progress-bar-label">
        <span>Skill Match Progress</span>
        <span>${data.present_skills.length} / ${data.present_skills.length + data.missing_skills.length} skills</span>
      </div>
      <div class="progress-track">
        <div class="progress-fill" id="progressFill"></div>
      </div>
    </div>

    <!-- Present Skills -->
    <div class="results-animate">
      <div class="section-title">
        Skills You Have
        <span class="tag tag-green">${data.present_skills.length} matched</span>
      </div>
      ${data.present_skills.length > 0
        ? `<div class="present-skills-list">
            ${data.present_skills.map(s =>
              `<span class="present-chip">${escHtml(s)}</span>`
            ).join("")}
           </div>`
        : `<p style="color:var(--text-3);font-size:14px;margin-bottom:40px;">No matching skills found yet — that's totally fine, we'll build from the ground up!</p>`
      }
    </div>

    <!-- Missing Skills -->
    <div class="results-animate">
      <div class="section-title">
        Skills to Learn
        <span class="tag tag-red">${data.missing_skills.length} gaps</span>
      </div>
      ${data.missing_skills.length === 0
        ? renderAllPresent()
        : `<div class="missing-skills-list">
            ${data.missing_skills.map((skill, i) => renderMissingSkill(skill, i)).join("")}
           </div>`
      }
    </div>

    <!-- Roadmap -->
    ${data.roadmap.length > 0 ? `
    <div class="roadmap-section results-animate">
      <div class="section-title">
        Your Learning Roadmap
        <span class="tag tag-blue">${data.roadmap.length} steps</span>
      </div>
      <p style="color:var(--text-3);font-size:14px;margin-bottom:28px;">
        Each step is ordered by learning priority. The AI explains <em style="color:var(--text-2)">why</em> each skill appears exactly where it does.
      </p>
      <div class="roadmap-timeline" id="roadmapTimeline">
        ${data.roadmap.map(step => renderRoadmapStep(step)).join("")}
      </div>
      <div class="total-time-banner">
        <div>
          <div class="total-time-label">Total Estimated Time</div>
          <div class="total-time-note">studying consistently ~10 hrs/week</div>
        </div>
        <div style="text-align:right">
          <div class="total-time-value">${data.total_weeks} weeks</div>
          <div class="total-time-note">≈ ${Math.round(data.total_weeks / 4)} months</div>
        </div>
      </div>
    </div>
    ` : ""}

  `;

  // Show section
  section.hidden = false;
  section.scrollIntoView({ behavior: "smooth", block: "start" });

  // Animate progress bar with delay
  setTimeout(() => {
    const fill = document.getElementById("progressFill");
    if (fill) fill.style.width = `${data.match_score}%`;
  }, 300);

  // Stagger roadmap step reveals
  setTimeout(() => {
    const steps = document.querySelectorAll(".roadmap-step");
    steps.forEach((step, i) => {
      setTimeout(() => step.classList.add("visible"), i * 80);
    });
  }, 400);

  // Wire up missing skill expand/collapse
  document.querySelectorAll(".missing-skill-card").forEach(card => {
    card.addEventListener("click", () => {
      const panel = card.querySelector(".xai-panel");
      const isOpen = panel.classList.contains("open");
      // Close all
      document.querySelectorAll(".xai-panel").forEach(p => p.classList.remove("open"));
      document.querySelectorAll(".missing-skill-card").forEach(c => c.classList.remove("expanded"));
      // Toggle clicked
      if (!isOpen) {
        panel.classList.add("open");
        card.classList.add("expanded");
      }
    });
  });
}


// ── Component Renderers ───────────────────────────────────────────────────────
function renderMissingSkill(skill, index) {
  const priorityLabel = skill.priority.charAt(0).toUpperCase() + skill.priority.slice(1);
  return `
    <div class="missing-skill-card" tabindex="0" role="button" aria-label="View explanation for ${escHtml(skill.name)}">
      <div class="priority-dot ${escHtml(skill.priority)}"></div>
      <div>
        <div class="missing-skill-name">${escHtml(skill.name)}</div>
        <div class="missing-skill-priority">${priorityLabel}</div>
      </div>
      <div class="missing-skill-weeks">~${skill.estimated_weeks}w</div>

      <!-- XAI Explanation Panel (hidden until click) -->
      <div class="xai-panel">
        <div class="xai-label">⬡ AI Explanation — Why this skill?</div>
        <p class="xai-reason">${escHtml(skill.reason)}</p>
        <div class="xai-resources-label">Recommended Resources</div>
        <div class="xai-resources">
          ${skill.resources.map(r => `<span class="xai-resource">${escHtml(r)}</span>`).join("")}
        </div>
      </div>
    </div>
  `;
}

function renderRoadmapStep(step) {
  return `
    <div class="roadmap-step ${escHtml(step.phase_key)}">
      <div class="step-node">${step.step}</div>
      <div class="step-card">
        <div class="step-phase">${escHtml(step.phase)}</div>
        <div class="step-skill">${escHtml(step.skill)}</div>
        <div class="step-xai">${escHtml(step.xai_explanation)}</div>
        <div class="step-meta">
          <span class="step-weeks">⏱ ~${step.estimated_weeks} weeks</span>
          <div class="step-resources">
            ${step.resources.slice(0, 2).map(r => `<span class="step-resource">${escHtml(r)}</span>`).join("")}
          </div>
        </div>
      </div>
    </div>
  `;
}

function renderAllPresent() {
  return `
    <div class="all-present-banner">
      <div class="all-present-icon">🎉</div>
      <div class="all-present-title">You're Job-Ready!</div>
      <p style="color:var(--text-3);font-size:14px;">You have all the required skills for this career path.</p>
    </div>
  `;
}


// ── Utility ───────────────────────────────────────────────────────────────────
function escHtml(str) {
  if (typeof str !== "string") return String(str);
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}