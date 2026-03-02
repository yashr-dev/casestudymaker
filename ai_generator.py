"""
DigiChefs Case Study Content Generator
Uses Gemini AI to transform basic inputs into Deep-style case study content.
"""

import json
import google.generativeai as genai
from duckduckgo_search import DDGS

def get_brand_research(brand_name: str) -> str:
    """Perform a web search to gather latest information about the brand."""
    try:
        results = DDGS().text(f"{brand_name} company overview business", max_results=3)
        if not results:
            return "No recent search results found."
        
        info = []
        for r in results:
            info.append(f"Title: {r.get('title')}\nSnippet: {r.get('body')}")
        return "\n\n".join(info)
    except Exception as e:
        print(f"Search failed: {e}")
        return "Search failed or unavailable."


def get_website_research(website_url: str) -> str:
    """Scrape a brand's website to gather information about the company."""
    if not website_url:
        return ""
    try:
        import urllib.request
        import re
        req = urllib.request.Request(website_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
        # Strip HTML tags to get text content
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        # Limit to first 3000 chars to keep it reasonable
        return text[:3000]
    except Exception as e:
        print(f"Website scrape failed: {e}")
        return f"Could not read website: {str(e)}"


SYSTEM_PROMPT = """You are Deep Mehta, the founder of DigiChefs, a digital marketing agency.
You are personally writing a case study for a brand. Your writing style is compelling and strategic — elevated but always grounded in real facts.

=== TONE ===
Medium-flowery. Confident, strategic, impactful.
- GOOD: "Sitting on untapped potential, their social media didn't reflect the legacy of the brand, and reach was stalling despite strong products."
- GOOD: "Mumbai's definitive sandwich authority — a brand that had been crafting sandwiches since 1986."
- BAD: "best-in-class growth hacking leveraging synergies across channels"
- BAD: "The brand had low engagement." (too dry)

=== ANTI-HALLUCINATION RULES (NUMBERS ONLY) ===
1. You MUST NOT invent, fabricate, or extrapolate ANY numbers, statistics, KPIs, or results not provided by the user.
2. You MUST NOT invent client testimonials or quotes. If none provided → ''.
3. You MUST NOT rename or relabel the type of campaign. Use the user's own words.
4. If the user didn't provide data for a field, return '' (empty string).

HOWEVER: For NARRATIVE sections (about_brand, challenge, core_insight, strategy, delivery_solution), you SHOULD write compelling, strategic, elevated prose. You may use web research to enrich the About Brand section with real public info. You may craft a strong narrative around the user's inputs. Just don't invent NUMBERS or METRICS.

=== SOP: TITLE ===
Format: Client name + Measurable outcome + Campaign/service description (2-3 words) + Duration
Examples:
- "25X Increase In Reach & 12X Increase In Engagement | Revamping Sunhalt Gold's Social Media Strategy"
- "Elevating A BMW Dealership From #11 To #1 In Digital Car Sales Using Performance Marketing in 2 Years"
Don'ts: No 'DigiChefs' in title, no random %, K/M must be CAPITALIZED, no specific YEAR (use durations).

=== SOP: ABOUT THE BRAND (Flowing paragraph — NO bullets) ===
Write a compelling 50-80 word paragraph covering:
- What the brand does and their positioning
- How big they are (scale, reach, history, locations)
- Top achievements or social proof
Use web research and website data to enrich this. Make the reader feel this brand deserves a case study.

=== SOP: CHALLENGE / THOUGHT BEHIND (Flowing paragraph — NO bullets) ===
Write a 50-80 word paragraph describing:
- What problem was the client facing
- Why this was a real business constraint (not just a marketing one)
- What made this hard
Must be specific to THIS brand — not generic marketing talk.

=== SOP: CORE INSIGHT (Flowing paragraph — NO bullets) ===
Write a 50-80 word paragraph covering:
- The research and diagnosis that led to the strategy
- The "aha moment" — the key realization
- Market/competitor learnings specific to this brand

=== SOP: STRATEGY (Flowing paragraph — NO bullets) ===
Write a 50-80 word paragraph describing:
- What was prioritized and why
- Channel mix logic and trade-offs
- Must show strategic thinking — WHY this approach, not just WHAT was done
- Include campaign duration if provided

=== SOP: DELIVERY / EXECUTION (Flowing paragraph — NO bullets) ===
Write a 50-80 word paragraph describing the key activities and rationale:
- What activities/formats did we execute (e.g., created a multi-platform social media solution, ran a festive campaign)
- WHY those activities were chosen (the rationale/strategic reasoning)
- Do NOT list a chronological sequence of individual posts or creatives
- Do NOT describe posting schedules or content calendars
- Focus on the strategic WHAT and WHY, not the tactical step-by-step

=== GLOBAL FORMATTING RULE ===
NEVER use nested or multi-level bullets. No sub-bullets under bullets.
- BAD: '• Main point\n  • Sub-point' or '• • Nested bullet'
- GOOD: Each point is a single-level item or flowing prose
All sections must be either flowing paragraphs OR flat single-level lists. No nesting ever.

=== SOP: IMPACT (Numbered list: 1. 2. 3.) ===
Don'ts:
- Do NOT add any number that is too small or insignificant
- Do NOT add numbers ONLY in % without absolute context
- Do NOT invent ANY number
Do's:
- Major business outcome first
- Primary numbers (matching the title) next
- Secondary numbers after
- Include campaign duration
- Awards/press mentions if provided

You must return a JSON object (no markdown, no code fences) with these keys:

{
  "case_study_title": "Follow TITLE rules. Client name + outcome + description + duration.",
  "brand_name": "AS PROVIDED",
  "industry": "AS PROVIDED",
  "services_used": "AS PROVIDED",
  "kpi_1_number": "Primary KPI from USER DATA. Capitalized K/M. '' if not provided.",
  "kpi_1_label": "Label. '' if not provided.",
  "kpi_2_number": "From USER DATA. '' if not provided.",
  "kpi_2_label": "'' if not provided.",
  "kpi_3_number": "From USER DATA. '' if not provided.",
  "kpi_3_label": "'' if not provided.",
  "about_brand": "FLOWING PARAGRAPH. 50-80 words. Use web research to enrich. No bullet points.",
  "challenge": "FLOWING PARAGRAPH. 50-80 words. Specific to this brand. No bullet points.",
  "core_insight": "FLOWING PARAGRAPH. 50-80 words. The aha moment and diagnosis. No bullet points.",
  "strategy": "FLOWING PARAGRAPH. 50-80 words. Strategic decisions and why. No bullet points.",
  "delivery_solution": "Brief 2-3 sentence overview of the solution approach.",
  "delivery_steps": "FLOWING PARAGRAPH. 50-80 words. Activities + rationale, NOT a posting sequence. No bullet points.",
  "tools_used": "Comma-separated IF mentioned. '' if not.",
  "impact_metrics": "NUMBERED LIST (1. 2. 3.) using ONLY user-provided data. Primary first, then secondary. Include duration.",
  "client_testimonial": "EXACT testimonial if provided. '' if not.",
  "learnings": "'' unless user mentioned.",
  "next_steps": "'' unless user mentioned.",
  "cta": "Soft, helpful CTA."
}

Return ONLY the JSON object."""


DEEP_QC_PROMPT = """You are Deep Mehta, founder of DigiChefs. You are reviewing a case study.
Your job: improve LANGUAGE and ensure SOP compliance. Make it impactful.

=== STRICT RULES ===
1. MUST NOT add new facts, numbers, or metrics not already present.
2. MUST NOT invent testimonials. '' stays ''.
3. MUST NOT fill empty fields with made-up content.
4. impact_metrics numbers must remain EXACTLY as-is.

=== TONE ===
Elevate the narrative sections (about_brand, challenge, core_insight, strategy) to be more compelling and strategic.
Make them read like an award-winning case study — confident, authoritative, with a storytelling arc.
But do NOT change any factual claims or numbers.

=== FORMAT ENFORCEMENT ===
- about_brand: Must be a FLOWING PARAGRAPH (50-80 words), not bullets
- challenge: Must be a FLOWING PARAGRAPH (50-80 words), not bullets
- core_insight: Must be a FLOWING PARAGRAPH (50-80 words), not bullets
- strategy: Must be a FLOWING PARAGRAPH (50-80 words), not bullets
- delivery_steps: Must be a FLOWING PARAGRAPH (50-80 words) about activities + rationale, NOT a bulleted posting sequence
- impact_metrics: Must be NUMBERED LIST (1. 2. 3.)
- NEVER use nested/multi-level bullets anywhere. No sub-bullets. All lists must be flat single-level.

=== TITLE CHECK ===
- Must NOT contain 'DigiChefs'
- K/M must be CAPITALIZED
- Must NOT mention specific YEAR
- Must include client name + measurable outcome

Return ONLY the RAW JSON object."""

def qc_case_study(content: dict, api_key: str = None) -> dict:
    """Pass the generated case study through the Deep Mehta QC Layer for profound improvements."""
    if api_key:
        genai.configure(api_key=api_key)
        
    user_prompt = f"Please review and elevate this case study JSON:\n\n{json.dumps(content, indent=2)}"
    
    model = genai.GenerativeModel(
        "gemini-2.0-flash",
        system_instruction=DEEP_QC_PROMPT
    )
    
    print("Running Deep Mehta QC Layer...")
    response = model.generate_content(
        user_prompt,
        generation_config=genai.GenerationConfig(
            temperature=0.6,
            response_mime_type="application/json"
        )
    )
    
    try:
        improved_content = json.loads(response.text)
    except json.JSONDecodeError:
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            text = text.rsplit("```", 1)[0]
        improved_content = json.loads(text)
        
    # Ensure media link is preserved through QC
    improved_content['media_link'] = content.get('media_link', '')
    return improved_content


def generate_case_study_content(
    brand_name: str,
    industry: str,
    services_used: str,
    what_we_did: str,
    how_we_did_it: str,
    impact: str,
    additional_context: str = "",
    rough_notes_content: str = "",
    user_clarifications: str = "",
    media_link: str = "",
    website_url: str = "",
    api_key: str = None
) -> dict:
    """
    Generate structured case study content using Gemini AI.
    """
    if api_key:
        genai.configure(api_key=api_key)
        
    print(f"Performing web research for {brand_name}...")
    brand_research = get_brand_research(brand_name)
    print("Research complete.")
    
    website_info = ""
    if website_url:
        print(f"Scraping brand website: {website_url}...")
        website_info = get_website_research(website_url)
        print("Website scrape complete.")
    
    user_prompt = f"""Create an impactful case study for this project. Write like you're crafting an award-winning submission.

BRAND: {brand_name}
INDUSTRY: {industry}

BRAND WEBSITE CONTENT:
{website_info if website_info else 'Not provided'}

WEB RESEARCH ON BRAND:
{brand_research}

INPUT FROM TEAM:
SERVICES USED: {services_used}
WHAT WE DID: {what_we_did}
HOW WE DID IT: {how_we_did_it}
IMPACT & RESULTS: {impact}
ADDITIONAL CONTEXT: {additional_context if additional_context else 'None'}

ROUGH NOTES / DRAFT (From Drive):
{rough_notes_content if rough_notes_content else 'None provided'}

CLARIFICATIONS FROM TEAM:
{user_clarifications if user_clarifications else 'None provided'}

MEDIA ASSETS LINK:
{media_link if media_link else 'None provided'}

Use the website content and web research to enrich the About Brand section with real facts (history, scale, achievements). For all other sections, synthesize the team's input into a compelling narrative. Remember: flowing paragraphs for narrative sections, bullet list for delivery steps, numbered list for impact. You are Deep Mehta — make this case study impactful."""

    model = genai.GenerativeModel(
        "gemini-2.0-flash",
        system_instruction=SYSTEM_PROMPT
    )
    
    response = model.generate_content(
        user_prompt,
        generation_config=genai.GenerationConfig(
            temperature=0.7,
            response_mime_type="application/json"
        )
    )
    
    try:
        content = json.loads(response.text)
    except json.JSONDecodeError:
        # Try to extract JSON from the response
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            text = text.rsplit("```", 1)[0]
        content = json.loads(text)
        
    # Inject media_link into the response dict to ensure it's available
    content['media_link'] = media_link
    
    # Pass through Deep QC Layer
    final_content = qc_case_study(content, api_key)
    
    return final_content

def generate_clarifying_questions(
    brand_name: str,
    industry: str,
    services_used: str,
    what_we_did: str,
    how_we_did_it: str,
    impact: str,
    additional_context: str = "",
    rough_notes_content: str = "",
    api_key: str = None
) -> list:
    """
    Generate 2-3 clarifying questions to ask the user if the input is sparse.
    """
    if api_key:
        genai.configure(api_key=api_key)
        
    print(f"Performing web research for {brand_name} for Clarification...")
    brand_research = get_brand_research(brand_name)
    
    prompt = f"""You are Deep Mehta, founder of DigiChefs.
A team member has brought you rough notes for a case study.
Before writing, you need to ask 2-3 specific questions to ensure the case study meets the DigiChefs SOP.

The SOP requires:
- TITLE: Client name + measurable business outcome + campaign description + duration
- ABOUT THE BRAND: What they do, how big they are, top achievements
- DELIVERY: In-depth strategic points, specific to this brand (not generic)
- IMPACT: Major business outcomes, primary numbers (absolute, not just %), campaign duration, awards/press
- CREATIVES: Screenshots from GA/Meta/Ads with engagement data

BRAND: {brand_name}
INDUSTRY: {industry}
LATEST RESEARCH ON BRAND:
{brand_research}

WHAT THEY PROVIDED (Form):
Services: {services_used}
What: {what_we_did}
How: {how_we_did_it}
Impact: {impact}
Context: {additional_context}

RAW ROUGH NOTES (From Drive):
{rough_notes_content if rough_notes_content else 'None provided'}

Analyze the inputs against the SOP requirements above. What is MISSING that would make this case study weak?
Focus on: Are the numbers impressive enough? Is there enough strategic depth? Is the campaign duration mentioned? Are there creatives/screenshots available?
Return ONLY a JSON array of strings containing your 2-3 questions. No markdown fences.
["Question 1?", "Question 2?"]"""

    model = genai.GenerativeModel(
        "gemini-2.0-flash"
    )
    
    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            temperature=0.7,
            response_mime_type="application/json"
        )
    )
    
    try:
        questions = json.loads(response.text)
        if not isinstance(questions, list):
            questions = [str(q) for q in questions.values()]
    except Exception:
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            text = text.rsplit("```", 1)[0]
        try:
            questions = json.loads(text)
        except:
            questions = ["What was the primary business objective beyond marketing metrics?", "Can you elaborate on the core insight that drove this campaign?"]
            
    return questions[:3]
