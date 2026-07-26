"""
app.py — SkillBridge Resume Analyzer Demo
Gradio frontend for the SkillBridge AI Service.
Deployed to Hugging Face Spaces.
"""

import os
import time
import uuid
import requests
import gradio as gr
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "https://your-service.onrender.com")
ANALYZE_ENDPOINT = f"{AI_SERVICE_URL}/v1/analyze-resume"
HEALTH_ENDPOINT = f"{AI_SERVICE_URL}/health"

TARGET_ROLES = [
    "Backend Engineer",
    "Frontend Engineer",
    "Full Stack Engineer",
    "AI/ML Engineer",
    "Cloud/DevOps Engineer",
]

PRIORITY_COLORS = {
    "CRITICAL": "#FF4B4B",
    "HIGH":     "#FF8C00",
    "MEDIUM":   "#FFC107",
    "LOW":      "#6C757D",
}

PRIORITY_EMOJI = {
    "CRITICAL": "🔴",
    "HIGH":     "🟠",
    "MEDIUM":   "🟡",
    "LOW":      "⚪",
}


# ── Service wake-up ───────────────────────────────────────────────────────────

def ping_service() -> str:
    """
    Ping the AI service health endpoint to warm it up.
    Render free tier spins down after inactivity — this fires on page load.
    """
    try:
        r = requests.get(HEALTH_ENDPOINT, timeout=5)
        if r.status_code == 200:
            return "✅ AI Service is online"
        return "⚠️ AI Service returned unexpected status"
    except requests.exceptions.Timeout:
        return "⏳ AI Service is waking up — your first analysis may take ~30 seconds"
    except Exception:
        return "⚠️ Could not reach AI Service — check deployment"


# ── Analysis call ─────────────────────────────────────────────────────────────

def analyze_resume(cv_file, target_role: str):
    """
    Send CV file to the FastAPI AI service and return formatted results.
    Called by Gradio on button click.
    """
    if cv_file is None:
        return (
            _score_html(None),
            _skills_html([], []),
            _gaps_html([]),
            _profile_html(None, [], ""),
            "⚠️ Please upload a CV file.",
        )

    if not target_role:
        return (
            _score_html(None),
            _skills_html([], []),
            _gaps_html([]),
            _profile_html(None, [], ""),
            "⚠️ Please select a target role.",
        )

    file_path = cv_file.name
    file_ext = Path(file_path).suffix.lower()

    if file_ext not in {".pdf", ".docx"}:
        return (
            _score_html(None),
            _skills_html([], []),
            _gaps_html([]),
            _profile_html(None, [], ""),
            f"⚠️ Unsupported file type: {file_ext}. Please upload a PDF or DOCX.",
        )

    request_id = str(uuid.uuid4())
    status_msg = f"⏳ Analyzing your CV against {target_role} market data..."

    try:
        with open(file_path, "rb") as f:
            files = {"file": (Path(file_path).name, f, _mime_type(file_ext))}
            data = {
                "user_id":     "demo_user",
                "target_role": target_role,
                "request_id":  request_id,
                "region":      "global",
            }
            response = requests.post(
                ANALYZE_ENDPOINT,
                files=files,
                data=data,
                timeout=120,  # CV analysis can take up to 60s
            )

        if response.status_code != 200:
            err = response.json().get("error", {})
            return (
                _score_html(None),
                _skills_html([], []),
                _gaps_html([]),
                _profile_html(None, [], ""),
                f"❌ Error {response.status_code}: {err.get('message', 'Unknown error')}",
            )

        result = response.json()
        if not result.get("success"):
            err = result.get("error", {})
            return (
                _score_html(None),
                _skills_html([], []),
                _gaps_html([]),
                _profile_html(None, [], ""),
                f"❌ {err.get('message', 'Analysis failed')}",
            )

        data = result["data"]
        processing_ms = result.get("meta", {}).get("processing_time_ms", 0)
        status_msg = f"✅ Analysis complete in {processing_ms / 1000:.1f}s"

        return (
            _score_html(data),
            _skills_html(data.get("skills", []), data.get("education", [])),
            _gaps_html(data.get("missing_skills", [])),
            _profile_html(
                data.get("experience_level"),
                data.get("education", []),
                data.get("summary", ""),
            ),
            status_msg,
        )

    except requests.exceptions.Timeout:
        return (
            _score_html(None),
            _skills_html([], []),
            _gaps_html([]),
            _profile_html(None, [], ""),
            "❌ Request timed out. The AI service may be starting up — please try again in 30 seconds.",
        )
    except Exception as e:
        return (
            _score_html(None),
            _skills_html([], []),
            _gaps_html([]),
            _profile_html(None, [], ""),
            f"❌ Unexpected error: {str(e)}",
        )


def _mime_type(ext: str) -> str:
    return "application/pdf" if ext == ".pdf" else \
           "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


# ── HTML renderers ────────────────────────────────────────────────────────────

def _score_html(data: dict | None) -> str:
    if data is None:
        return """
        <div style="text-align:center; padding:40px; background:#1a1a2e; border-radius:16px;">
            <p style="color:#666; font-size:16px; margin:0;">
                Upload your CV and select a role to see your score
            </p>
        </div>"""

    score = data.get("employability_score", 0)
    target_role = data.get("target_role", "")
    matched = data.get("matched_skills_count", 0)
    total = data.get("total_role_skills_analyzed", 0)

    # Score color
    if score >= 75:
        color = "#00C851"
        label = "Strong Match"
        ring_color = "#00C851"
    elif score >= 50:
        color = "#FFC107"
        label = "Developing"
        ring_color = "#FFC107"
    else:
        color = "#FF4B4B"
        label = "Needs Work"
        ring_color = "#FF4B4B"

    circumference = 2 * 3.14159 * 54
    offset = circumference * (1 - score / 100)

    return f"""
    <div style="text-align:center; padding:32px 20px; background:linear-gradient(135deg,#1a1a2e,#16213e);
                border-radius:16px; border:1px solid #0f3460;">

        <p style="color:#8892b0; font-size:13px; margin:0 0 16px 0; letter-spacing:2px; text-transform:uppercase;">
            Employability Score
        </p>

        <svg width="140" height="140" viewBox="0 0 140 140" style="margin:0 auto 16px auto; display:block;">
            <circle cx="70" cy="70" r="54" fill="none" stroke="#0f3460" stroke-width="12"/>
            <circle cx="70" cy="70" r="54" fill="none" stroke="{ring_color}" stroke-width="12"
                    stroke-dasharray="{circumference:.1f}" stroke-dashoffset="{offset:.1f}"
                    stroke-linecap="round" transform="rotate(-90 70 70)"
                    style="transition: stroke-dashoffset 1s ease;"/>
            <text x="70" y="65" text-anchor="middle" fill="{color}"
                  font-size="32" font-weight="bold" font-family="Arial">{score}</text>
            <text x="70" y="85" text-anchor="middle" fill="#8892b0"
                  font-size="12" font-family="Arial">out of 100</text>
        </svg>

        <p style="color:{color}; font-size:18px; font-weight:bold; margin:0 0 8px 0;">{label}</p>
        <p style="color:#8892b0; font-size:13px; margin:0 0 20px 0;">vs {target_role} requirements</p>

        <div style="display:flex; justify-content:center; gap:32px;">
            <div>
                <p style="color:#ccd6f6; font-size:22px; font-weight:bold; margin:0;">{matched}</p>
                <p style="color:#8892b0; font-size:12px; margin:4px 0 0 0;">Skills Matched</p>
            </div>
            <div style="width:1px; background:#0f3460;"></div>
            <div>
                <p style="color:#ccd6f6; font-size:22px; font-weight:bold; margin:0;">{total}</p>
                <p style="color:#8892b0; font-size:12px; margin:4px 0 0 0;">Role Skills Tracked</p>
            </div>
            <div style="width:1px; background:#0f3460;"></div>
            <div>
                <p style="color:#ccd6f6; font-size:22px; font-weight:bold; margin:0;">{total - matched}</p>
                <p style="color:#8892b0; font-size:12px; margin:4px 0 0 0;">Gaps Found</p>
            </div>
        </div>
    </div>"""


def _skills_html(skills: list, education: list) -> str:
    if not skills and not education:
        return "<div style='padding:20px; color:#666;'>No skills data yet.</div>"

    skill_tags = ""
    for skill in skills:
        name = skill.get("name", "").title()
        cat = skill.get("category", "general")
        cat_colors = {
            "frontend": "#3D5AFE",
            "backend":  "#00897B",
            "devops":   "#F57C00",
            "ai_ml":    "#8E24AA",
            "general":  "#455A64",
        }
        color = cat_colors.get(cat, "#455A64")
        skill_tags += f"""
        <span style="display:inline-block; background:{color}22; color:{color};
                     border:1px solid {color}44; border-radius:20px;
                     padding:4px 12px; margin:4px; font-size:13px; font-weight:500;">
            {name}
        </span>"""

    edu_html = ""
    for edu in education:
        inst = edu.get("institution", "")
        deg = edu.get("degree", "")
        if inst or deg:
            edu_html += f"""
            <div style="padding:10px 14px; background:#0f3460; border-radius:8px;
                        margin-bottom:8px; border-left:3px solid #3D5AFE;">
                <p style="color:#ccd6f6; font-weight:600; margin:0 0 2px 0;">{deg}</p>
                <p style="color:#8892b0; font-size:13px; margin:0;">{inst}</p>
            </div>"""

    return f"""
    <div style="background:#1a1a2e; border-radius:16px; padding:24px;
                border:1px solid #0f3460;">
        <h3 style="color:#ccd6f6; margin:0 0 16px 0; font-size:15px;
                   letter-spacing:1px; text-transform:uppercase;">✅ Your Skills</h3>
        <div style="margin-bottom:24px;">{skill_tags or '<p style="color:#666;">No skills extracted</p>'}</div>

        {"<h3 style='color:#ccd6f6; margin:0 0 12px 0; font-size:15px; letter-spacing:1px; text-transform:uppercase;'>🎓 Education</h3>" + edu_html if edu_html else ""}
    </div>"""


def _gaps_html(missing_skills: list) -> str:
    if not missing_skills:
        return """
        <div style="background:#1a1a2e; border-radius:16px; padding:24px;
                    border:1px solid #0f3460; text-align:center;">
            <p style="color:#00C851; font-size:16px;">🎉 No major skill gaps found!</p>
        </div>"""

    cards = ""
    for gap in missing_skills:
        skill = gap.get("name", "").title()
        priority = gap.get("priority", "LOW")
        pct = gap.get("affected_roles_pct", 0)
        reasoning = gap.get("reasoning", "")
        color = PRIORITY_COLORS.get(priority, "#6C757D")
        emoji = PRIORITY_EMOJI.get(priority, "⚪")

        bar_width = min(pct, 100)

        cards += f"""
        <div style="background:#16213e; border-radius:12px; padding:16px;
                    margin-bottom:12px; border-left:4px solid {color};
                    border:1px solid #0f3460; border-left:4px solid {color};">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <span style="color:#ccd6f6; font-weight:600; font-size:15px;">{emoji} {skill}</span>
                <span style="background:{color}22; color:{color}; border:1px solid {color}44;
                             border-radius:12px; padding:2px 10px; font-size:12px; font-weight:600;">
                    {priority}
                </span>
            </div>

            <div style="margin-bottom:10px;">
                <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                    <span style="color:#8892b0; font-size:12px;">Market Demand</span>
                    <span style="color:{color}; font-size:12px; font-weight:600;">{pct}% of job postings</span>
                </div>
                <div style="background:#0f3460; border-radius:4px; height:6px; overflow:hidden;">
                    <div style="background:{color}; height:100%; width:{bar_width}%;
                                border-radius:4px; transition:width 1s ease;"></div>
                </div>
            </div>

            <p style="color:#8892b0; font-size:13px; margin:0; line-height:1.5;">
                {reasoning}
            </p>
        </div>"""

    return f"""
    <div style="background:#1a1a2e; border-radius:16px; padding:24px;
                border:1px solid #0f3460;">
        <h3 style="color:#ccd6f6; margin:0 0 16px 0; font-size:15px;
                   letter-spacing:1px; text-transform:uppercase;">
            ❌ Skill Gaps  <span style="color:#8892b0; font-weight:normal;">({len(missing_skills)} found)</span>
        </h3>
        {cards}
    </div>"""


def _profile_html(experience_level: str | None, education: list, summary: str) -> str:
    if not experience_level and not summary:
        return "<div style='padding:20px; color:#666;'>No profile data yet.</div>"

    exp_colors = {
        "BEGINNER":     ("#3D5AFE", "Entry Level"),
        "INTERMEDIATE": ("#FFC107", "Mid Level"),
        "ADVANCED":     ("#00C851", "Senior Level"),
    }
    exp_color, exp_label = exp_colors.get(experience_level or "", ("#666", "Unknown"))

    return f"""
    <div style="background:#1a1a2e; border-radius:16px; padding:24px;
                border:1px solid #0f3460;">
        <h3 style="color:#ccd6f6; margin:0 0 16px 0; font-size:15px;
                   letter-spacing:1px; text-transform:uppercase;">👤 Profile Summary</h3>

        <div style="display:flex; align-items:center; gap:12px; margin-bottom:16px;">
            <span style="background:{exp_color}22; color:{exp_color};
                         border:1px solid {exp_color}44; border-radius:20px;
                         padding:6px 16px; font-size:14px; font-weight:600;">
                {exp_label}
            </span>
        </div>

        {f'<p style="color:#a8b2d8; font-size:14px; line-height:1.7; margin:0;">{summary}</p>' if summary else ""}
    </div>"""


# ── Gradio UI ─────────────────────────────────────────────────────────────────

CSS = """
body, .gradio-container {
    background: #0d1117 !important;
    font-family: 'Inter', Arial, sans-serif !important;
}
.gr-button-primary {
    background: linear-gradient(135deg, #3D5AFE, #651FFF) !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    padding: 12px 24px !important;
    color: white !important;
}
.gr-button-primary:hover {
    background: linear-gradient(135deg, #536DFE, #7C4DFF) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 20px rgba(61, 90, 254, 0.4) !important;
}
.gr-upload {
    background: #161b22 !important;
    border: 2px dashed #30363d !important;
    border-radius: 12px !important;
}
footer { display: none !important; }
"""

with gr.Blocks(css=CSS, title="SkillBridge — Resume Analyzer") as demo:

    # ── Header ────────────────────────────────────────────────────────────────
    gr.HTML("""
    <div style="text-align:center; padding:40px 20px 24px; background:linear-gradient(180deg,#1a1a2e,transparent);">
        <h1 style="color:#ccd6f6; font-size:36px; font-weight:800; margin:0 0 8px 0;
                   letter-spacing:-1px;">
            Skill<span style="color:#3D5AFE;">Bridge</span>
        </h1>
        <p style="color:#8892b0; font-size:16px; margin:0 0 8px 0;">
            AI-powered resume analysis against real market data
        </p>
        <p style="color:#4a5568; font-size:13px; margin:0;">
            Powered by Gemini · Market data from 500+ real job postings
        </p>
    </div>
    """)

    # ── Service status ────────────────────────────────────────────────────────
    service_status = gr.HTML(value="⏳ Connecting to AI service...")

    # ── Input section ─────────────────────────────────────────────────────────
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 📄 Upload Your CV")
            cv_input = gr.File(
                label="CV File",
                file_types=[".pdf", ".docx"],
                file_count="single",
            )
            role_input = gr.Dropdown(
                choices=TARGET_ROLES,
                label="Target Role",
                info="Which role are you applying for?",
                value=None,
            )
            analyze_btn = gr.Button(
                "✨ Analyze My Resume",
                variant="primary",
                size="lg",
            )
            status_output = gr.Textbox(
                label="Status",
                interactive=False,
                show_label=False,
                placeholder="Status will appear here...",
            )

        # ── Score panel ───────────────────────────────────────────────────────
        with gr.Column(scale=1):
            score_output = gr.HTML(
                value="""
                <div style="text-align:center; padding:40px; background:#1a1a2e;
                            border-radius:16px; border:1px solid #0f3460;">
                    <p style="color:#4a5568; font-size:15px; margin:0;">
                        Your employability score will appear here
                    </p>
                </div>"""
            )

    # ── Results section ───────────────────────────────────────────────────────
    gr.Markdown("---")
    gr.Markdown("### 📊 Analysis Results")

    with gr.Tabs():
        with gr.Tab("❌ Skill Gaps"):
            gaps_output = gr.HTML(
                value="<div style='padding:20px; color:#4a5568;'>Run an analysis to see your skill gaps.</div>"
            )
        with gr.Tab("✅ Your Skills"):
            skills_output = gr.HTML(
                value="<div style='padding:20px; color:#4a5568;'>Run an analysis to see your extracted skills.</div>"
            )
        with gr.Tab("👤 Profile"):
            profile_output = gr.HTML(
                value="<div style='padding:20px; color:#4a5568;'>Run an analysis to see your profile summary.</div>"
            )

    # ── Footer ────────────────────────────────────────────────────────────────
    gr.HTML("""
    <div style="text-align:center; padding:32px 20px 16px; color:#4a5568; font-size:13px;">
        Built with FastAPI · Gemini · Qdrant · pdfplumber<br>
        Market data sourced from real job postings via JSearch API
    </div>
    """)

    # ── Event handlers ────────────────────────────────────────────────────────
    demo.load(
        fn=ping_service,
        inputs=None,
        outputs=service_status,
    )

    analyze_btn.click(
        fn=analyze_resume,
        inputs=[cv_input, role_input],
        outputs=[score_output, skills_output, gaps_output, profile_output, status_output],
        show_progress=True,
    )




if __name__ == "__main__":
    import os
    # Get the PORT environment variable injected by Railway (default to 7860 if missing)
    port = int(os.environ.get("PORT", 7860))
    
    demo.launch(
        server_name="0.0.0.0",  # Crucial for cloud platforms like Railway/Render
        server_port=port
    )
