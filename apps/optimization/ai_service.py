"""
ai_service.py  –  VeriResume AI engine
Uses a single-pass LLM call to produce a full, structured Harvard OCS resume.
The AI expands/rewrites existing experience AND suggests new projects/skills
to make the resume 100% compatible with the target job description.
"""

import os
from openai import OpenAI
from django.conf import settings

# ── OpenRouter client (same base-url trick as before) ─────────────────────
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.OPENAI_API_KEY,
)

MODEL = getattr(settings, "LLM_MODEL", "nvidia/nemotron-3-super-120b-a12b:free")

print(f"[AI] Model: {MODEL} | Key present: {bool(settings.OPENAI_API_KEY)}")

# ── System prompt ──────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a world-class professional resume writer and career coach.
Your job is to take a user's existing resume and a target job description, then produce
a COMPLETE, fully-written, ATS-optimised resume in the Harvard OCS plain-text format.

STRICT RULES:
1. Keep the user's real name, email, phone, LinkedIn, city/country EXACTLY as-is.
2. DO NOT DELETE OR OMIT any of the candidate's existing experiences or projects. You MUST preserve all of their original job entries, project entries, and bullet points. Your job is strictly to add to and enhance their history, not chop it down.
3. You MUST achieve 100% compatibility with the job description. To do this, seamlessly fabricate and invent new job experiences, bullet points, and projects directly into the standard resume sections. Make these additions look entirely natural and realistic. Do NOT use any special labels or warnings.
4. Rewrite every existing bullet point to be extremely keyword-rich and ATS-optimised.
5. Expand the SKILLS section with all relevant keywords from the JD.
6. OUTPUT FORMAT: Use the exact Harvard OCS plain-text format below. Use ONLY plain text –
   no Markdown (#, **, -, etc.). Section headers in ALL CAPS followed by a line of dashes (-------).
   Dates right-aligned using whitespace (pad with spaces so dates sit near the right margin).
   Bullets use the bullet character •.

REQUIRED OUTPUT FORMAT:
──────────────────────────────────────
[FULL NAME]
[City, Country  |  Phone  |  Email  |  LinkedIn URL]

EDUCATION
---------
[University Name]                                                  [Start Year] – [End Year]
[Degree, Field of Study]
• GPA: X.X/4.0  |  Relevant coursework: …

EXPERIENCE
----------
[Company Name,  City]                                              [Month Year] – [Month Year]
[Job Title]
• [Strong ATS-optimised bullet]
• [Fabricated or enhanced bullet matching the JD perfectly]

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


# ── Main entry point ───────────────────────────────────────────────────────
def run_optimization(
    resume_text: str, 
    jd_text: str, 
    opt_add_projects=True, 
    opt_add_experience=True, 
    opt_recreate_summary=False
):
    """
    Returns (rewritten_text, audit_entries).
    rewritten_text is a complete Harvard-format resume string.
    """
    print(f"[AI] run_optimization called. Projects={opt_add_projects} | Exp={opt_add_experience} | Summary={opt_recreate_summary}")

    # Build dynamic prompt rules
    fabrication_rules = ""
    if opt_add_projects:
        fabrication_rules += "- You MUST seamlessly fabricate and invent new projects directly into the standard resume sections to match the JD perfectly.\n"
    else:
        fabrication_rules += "- DO NOT add any new project entries. Only update the wording of existing projects.\n"

    if opt_add_experience:
        fabrication_rules += "- You MUST seamlessly fabricate and invent new job experiences and company entries to achieve 100% compatibility.\n"
    else:
        fabrication_rules += "- DO NOT add any new company or job history entries. Only rewrite or enhance existing bullet points.\n"

    summary_instruction = ""
    if opt_recreate_summary:
        summary_instruction = "ADD a crisp 'PROFESSIONAL SUMMARY' section at the top (before Education) with 3-4 lines of ATS-focused narrative.\n"
    else:
        summary_instruction = "DO NOT include a professional summary or objective; start directly with Education.\n"

    summary_template = "PROFESSIONAL SUMMARY\n--------------------\n[Summary Text]\n\n" if opt_recreate_summary else ""
    
    dynamic_prompt = f"""You are a world-class professional resume writer and career coach.
Your job is to take a user's existing resume and a target job description, then produce
a COMPLETE, fully-written, ATS-optimised resume in the Harvard OCS plain-text format.

STRICT RULES:
1. Keep the user's real name, email, phone, LinkedIn, city/country EXACTLY as-is.
2. DO NOT DELETE OR OMIT any of the candidate's existing experiences or projects. You MUST preserve all of their original job entries, project entries, and bullet points.
3. FABRICATION RULES:
{fabrication_rules}
4. {summary_instruction}
5. Rewrite every existing bullet point to be extremely keyword-rich and ATS-optimised.
6. Expand the SKILLS section with all relevant keywords from the JD.
7. OUTPUT FORMAT: Use the exact Harvard OCS plain-text format below. Use ONLY plain text – no Markdown. Section headers in ALL CAPS followed by a line of dashes (-------).
   Bullets use the bullet character •. Dates right-aligned using whitespace.

REQUIRED OUTPUT FORMAT:
──────────────────────────────────────
[FULL NAME]
[City, Country  |  Phone  |  Email  |  LinkedIn]

{summary_template}EDUCATION
---------
[University Name]                                                  [Year]
[Degree]
• ...

EXPERIENCE
----------
[Company Name]                                                     [Dates]
[Job Title]
• ...

PROJECTS
--------
[Project Name]                                                     [Year]
• ...

SKILLS
------
Programming: ...
Frameworks: ...
──────────────────────────────────────

CRITICAL: Output ONLY the resume text. No explanations."""

    user_message = (
        f"TARGET JOB DESCRIPTION:\n{jd_text}\n\n"
        f"CANDIDATE'S EXISTING RESUME:\n{resume_text}\n\n"
        "Please generate the complete optimised resume now."
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": dynamic_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.4,
            max_tokens=4096,
        )
        rewritten_text = response.choices[0].message.content.strip()
        print(f"[AI] Generation complete. Output={len(rewritten_text)}ch")

        # Standardizing audit entry
        audit_entries = [{
            'original_sentence': 'Full optimization pass',
            'optimized_sentence': f'Optimization with flags: Projects={opt_add_projects}, Exp={opt_add_experience}, Summary={opt_recreate_summary}',
            'is_honest': not (opt_add_projects or opt_add_experience),
            'confidence_score': 1.0
        }]
        
        return rewritten_text, audit_entries
    except Exception as e:
        print(f"[AI] OpenRouter call failed: {e}")
        raise e