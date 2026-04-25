import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from dotenv import load_dotenv
from src.ai_engine import ask_gemini

load_dotenv()

def _gemini_email(company_name, niche, analysis, location, sender_name):
    """Attempt Gemini-powered email. Returns dict or None."""
    pains = "\n".join(f"- {p}" for p in analysis.get("hard_pain_points", [])[:3])
    leak = analysis.get("estimated_revenue_leak", "significant revenue")
    prompt = (
        f"Write a short, highly personalised cold outreach email from {sender_name} (AI Strategy Consultant) "
        f"to the {niche} business '{company_name}' in {location}.\n"
        f"Their specific pain points are:\n{pains}\n"
        f"Estimated monthly revenue leak: {leak}\n"
        f"Rules: subject line first (prefix with 'Subject: '), then blank line, then body. "
        f"Max 180 words. No bullet lists. Conversational, not salesy. End with a soft CTA for a quick call."
    )
    result = ask_gemini(prompt)
    if not result:
        return None
    lines = result.split("\n", 2)
    subject = lines[0].replace("Subject:", "").strip() if lines else f"Question for {company_name}"
    body = "\n".join(lines[2:]).strip() if len(lines) > 2 else result
    return {"subject": subject, "body": body}

def generate_personalized_email(company_name, niche, analysis, location="your area"):
    """
    True Personalization Engine: Crafts a unique email based on each business's 
    specific audit findings (pains, gaps, and revenue leaks).
    """
    clean_name = company_name.split(',')[0].strip()
    pains = analysis.get("hard_pain_points", [])
    market_gap = analysis.get("market_gap_analysis", "")
    leak = analysis.get("estimated_revenue_leak", "a significant chunk of revenue")
    friction = analysis.get("conversion_friction", "")
    fomo = analysis.get("fomo_intelligence", "")

    sender_name = os.getenv("YOUR_NAME", "Pranshu Mishra")

    # Try Gemini-powered email first
    gemini_result = _gemini_email(clean_name, niche, analysis, location, sender_name)
    if gemini_result:
        return gemini_result

    # 1. Subject Line: Highly specific (static fallback)
    subject = f"Question for {clean_name}"
    
    # 2. Body: Hooking them with their unique audit data
    body = f"Hi {clean_name} Team,\n\n"
    
    # The Market Context Hook
    body += f"I was looking into the {niche.lower()} market in {location} and noticed something that might interest you: {market_gap}\n\n"
    
    # The Audit Reveal
    body += f"I ran a quick digital audit on your actual practice and found a few specific bottlenecks that are likely affecting your conversion rates:\n\n"
    
    for p in pains[:3]: # Focus on the top 3 specific pains found
        body += f"  - {p}\n"
    
    if friction:
        body += f"\nWhat concerns me most is the conversion friction: {friction}\n\n"

    # The Impact (The 'Why')
    body += f"Individually these gaps seem small, but together they represent an estimated monthly revenue leak of {leak} for a practice of your size.\n\n"
    
    # FOMO Intelligence (Market position)
    if fomo:
        body += f"{fomo}\n\n"
        
    # Value Proposition: Dynamic based on findings
    body += "We’ve been helping businesses bridge these gaps quietly—without adding workload—by:\n"
    
    has_custom_bullets = False
    if any("reviews" in p.lower() for p in pains):
        body += "* Turning trust signals into an automated asset via review systems\n"
        has_custom_bullets = True
    if any("booking" in p.lower() or "scheduling" in p.lower() for p in pains):
        body += "* Capturing 24/7 demand with AI-assisted intake frameworks\n"
        has_custom_bullets = True
    if any("reactivation" in p.lower() for p in pains):
        body += "* Automating patient reactivation to bring dormant records back to life\n"
        has_custom_bullets = True
        
    if not has_custom_bullets:
        body += "* Implementing AI automation to capture high-intent patients\n"
        body += "* Reducing digital friction points to improve booking conversion\n"

    body += "\nIf you're open, I can walk you through the full breakdown and show you the exact numbers.\n\n"
    body += f"Best,\n{sender_name}"
    
    return {
        "subject": subject,
        "body": body
    }

def generate_outreach(input_file="data/researched_leads.json", output_file="data/outbox.json"):
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        leads = json.load(f)

    outbox = []
    for lead in leads:
        # Pass location (e.g. "Birmingham, AL") to the generator
        email = generate_personalized_email(
            lead['name'], 
            lead.get('niche', 'Dental'), 
            lead['analysis'], 
            lead.get('location', 'your area')
        )
        lead['email_draft'] = email
        outbox.append(lead)
        
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(outbox, f, indent=4)
    print(f"SUCCESS: Personalized FOMO drafting complete for {len(outbox)} leads.")

if __name__ == "__main__":
    generate_outreach()
