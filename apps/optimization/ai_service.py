"""
ai_service.py  –  VeriResume AI engine
Uses a single-pass LLM call to produce a full, structured Harvard OCS resume.
The AI expands/rewrites existing experience AND suggests new projects/skills
to make the resume 100% compatible with the target job description.
"""

import os
from openai import OpenAI
from django.conf import settings

# ── OpenRouter client ───────────────────────────────────────────────────────
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.OPENAI_API_KEY,
)

MODEL = getattr(settings, "LLM_MODEL", "inclusionai/ling-2.6-flash:free")

# ── List of fallback models ─────────────────────────────────────────────────
MODELS_TO_TRY = [
    MODEL,
    "google/gemini-2.0-flash-exp:free",
    "mistralai/mistral-7b-instruct:free",
    "microsoft/phi-3-medium-128k-instruct:free",
]


# ── Helper: infer job title from JD ────────────────────────────────────────
def infer_job_title(jd_text: str) -> str:
    """
    If the user did not provide a target job title, call the LLM with a
    lightweight single-sentence prompt to extract the best job title from
    the job description. Returns a clean string like "Senior Software Engineer".
    """
    prompt = (
        "Extract the single most specific job title from the job description below. "
        "Return ONLY the job title, nothing else — no explanation, no punctuation, no quotes.\n\n"
        f"JOB DESCRIPTION:\n{jd_text[:2000]}"  # Limit context for speed
    )

    last_error = None
    for current_model in MODELS_TO_TRY:
        try:
            response = client.chat.completions.create(
                model=current_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=30,
            )
            if response and response.choices:
                title = response.choices[0].message.content.strip().strip('"').strip("'")
                if title:
                    return title
        except Exception as e:
            last_error = e
            continue

    return "Software Engineer"  # Safe default if all models fail


# ── Main entry point ────────────────────────────────────────────────────────
def run_optimization(
    resume_text: str,
    jd_text: str,
    target_job_title: str = "",
    opt_add_projects=True,
    opt_add_experience=True,
    opt_recreate_summary=False,
):
    """
    Returns (rewritten_text, audit_entries, resolved_job_title).
    rewritten_text is a complete Harvard-format resume string.
    resolved_job_title is the final title used (user's or auto-inferred).
    """
    rewritten_text = ""

    # ── Auto-infer job title if user left it blank ─────────────────────────
    resolved_title = target_job_title.strip()
    if not resolved_title:
        resolved_title = infer_job_title(jd_text)

    # ── Build dynamic fabrication rules ───────────────────────────────────
    fabrication_rules = ""
    if opt_add_experience:
        fabrication_rules += (
            "- You MUST fabricate NEW job experience entries to achieve 100% JD compatibility. "
            "CRITICAL: Spread the new skills across 2 to 3 SEPARATE, DISTINCT company entries "
            "(e.g., a startup, a mid-size firm, and a freelance/consulting role). "
            "Each company entry must focus on a DIFFERENT subset of the missing skills. "
            "DO NOT put all fabricated skills into a single company block. "
            "Each entry must have a realistic company name, city, job title, dates, and 3-5 strong bullet points.\n"
        )
    else:
        fabrication_rules += (
            "- DO NOT add any new company or job history entries. "
            "Only rewrite or enhance existing bullet points.\n"
        )

    if opt_add_projects:
        fabrication_rules += (
            "- You MUST add 2-3 new fabricated technical PROJECTS into the PROJECTS section "
            "that demonstrate the core technologies from the JD. "
            "Each project must have a unique name, tech stack, and 2-3 bullet points.\n"
        )
    else:
        fabrication_rules += (
            "- DO NOT add any new project entries. Only update the wording of existing projects.\n"
        )

    summary_instruction = ""
    if opt_recreate_summary:
        summary_instruction = (
            "ADD a 'PROFESSIONAL SUMMARY' section at the very top (before Education) "
            f"with 3-4 lines of ATS-focused narrative positioning the candidate as a strong {resolved_title}.\n"
        )
    else:
        summary_instruction = (
            "DO NOT include a professional summary or objective; start directly with Education.\n"
        )

    summary_template = "PROFESSIONAL SUMMARY\n--------------------\n[Summary Text]\n\n" if opt_recreate_summary else ""

    dynamic_prompt = f"""You are a world-class professional resume writer and career coach.
Your task: take the candidate's existing resume and the target job description, then produce
a COMPLETE, fully-written, ATS-optimised resume in the Harvard OCS plain-text format.

TARGET ROLE: {resolved_title}

STRICT RULES:
1. Keep the candidate's real name, email, phone, LinkedIn, city/country EXACTLY as-is.
2. DO NOT DELETE or omit any of the candidate's existing job entries, projects, or bullet points. Preserve all original content. You only ADD to and ENHANCE their history.
3. Rewrite every existing bullet point to be extremely keyword-rich and ATS-optimised for the TARGET ROLE.
4. Expand the SKILLS section with ALL relevant keywords and technologies from the JD.
5. {summary_instruction}
6. FABRICATION RULES (follow exactly):
{fabrication_rules}
7. OUTPUT FORMAT: Harvard OCS plain-text only. No Markdown (no #, **, -, etc.).
   Section headers in ALL CAPS followed by a line of dashes.
   Bullets use the bullet character •.
   Dates right-aligned using spaces (pad so dates sit near the right margin ~80 chars).

REQUIRED OUTPUT FORMAT:
──────────────────────────────────────
[FULL NAME]
[City, Country  |  Phone  |  Email  |  LinkedIn URL]

{summary_template}EDUCATION
---------
[University Name]                                                  [Start Year] – [End Year]
[Degree, Field of Study]
• GPA: X.X/4.0  |  Relevant coursework: …

EXPERIENCE
----------
[Company Name, City]                                               [Month Year] – [Month Year]
[Job Title]
• [Strong ATS-optimised bullet]
• [Fabricated or enhanced bullet matching the JD perfectly]
• [Another strong bullet]

[Company Name 2, City]                                             [Month Year] – [Month Year]
[Job Title 2]
• [Bullet focused on a DIFFERENT subset of JD skills]
• …

PROJECTS
--------
[Project Name]  |  [Tech Stack]                                    [Year]
• [What it does and its impact]

SKILLS
------
Programming: …
Frameworks: …
Tools & DevOps: …
Languages: …
──────────────────────────────────────

CRITICAL: Output ONLY the resume text. No explanations before or after. No markdown."""

    user_message = (
        f"TARGET JOB DESCRIPTION:\n{jd_text}\n\n"
        f"CANDIDATE'S EXISTING RESUME:\n{resume_text}\n\n"
        f"Please generate the complete optimised resume now for the role of {resolved_title}."
    )

    last_error = None

    for current_model in MODELS_TO_TRY:
        try:
            response = client.chat.completions.create(
                model=current_model,
                messages=[
                    {"role": "system", "content": dynamic_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.4,
                max_tokens=4096,
            )

            if not response or not hasattr(response, "choices") or not response.choices:
                continue

            rewritten_text = response.choices[0].message.content.strip()

            if not rewritten_text:
                continue

            audit_entries = [
                {
                    "original_sentence": "Full optimization pass",
                    "optimized_sentence": (
                        f"Optimization for '{resolved_title}' with flags: "
                        f"Projects={opt_add_projects}, Exp={opt_add_experience}, "
                        f"Summary={opt_recreate_summary}"
                    ),
                    "is_honest": not (opt_add_projects or opt_add_experience),
                    "confidence_score": 1.0,
                }
            ]

            return rewritten_text, audit_entries, resolved_title

        except Exception as e:
            last_error = e
            continue

    # All models failed
    if last_error:
        raise last_error
    raise ValueError("All AI models failed to return a valid response.")