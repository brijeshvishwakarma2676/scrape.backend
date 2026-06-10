from openai import AsyncOpenAI
from dotenv import load_dotenv
import os
import json

load_dotenv()

_api_key = os.getenv("OPENAI_API_KEY", "")
_base_url = "https://openrouter.ai/api/v1" if _api_key.startswith("sk-or-") else None

client = AsyncOpenAI(api_key=_api_key, base_url=_base_url)

PORTFOLIO = [
    {
        "url": "https://premium-dining-restaurant.vercel.app/",
        "tags": ["restaurant", "food", "cafe", "dining", "bakery", "catering", "hotel", "bar", "lounge", "biryani", "pizza", "sweets", "juice", "kitchen", "dhaba", "tiffin", "eatery"],
    },
    {
        "url": "https://premium-fitness-portfolio.vercel.app/",
        "tags": ["fitness", "gym", "workout", "crossfit", "sports", "martial arts", "boxing", "personal trainer", "health", "nutrition", "supplement", "physiotherapy", "rehab"],
    },
    {
        "url": "https://eg-earth-fitness-gym-portfolio.vercel.app/",
        "tags": ["fitness", "gym", "workout", "training", "crossfit", "sports", "health", "healthclub", "weightlifting", "personal trainer", "bodybuilding", "yoga"],
    },
    {
        "url": "https://healthcare-landing-page-directions.vercel.app/",
        "tags": ["hospital", "clinic", "doctor", "medical", "dentist", "healthcare", "health", "pharmacy", "ayurvedic", "homeopathy", "physiotherapist", "pathology", "lab", "diagnostic"],
    },
    {
        "url": "https://shopcanvas-multi-theme-ecommerce.vercel.app/",
        "tags": ["shop", "store", "retail", "ecommerce", "grocery", "supermarket", "boutique", "fashion", "clothing", "electronics", "hardware", "jewelry", "mart", "mall"],
    },
    {
        "url": "https://babaproperties.vercel.app/",
        "tags": ["real estate", "property", "properties", "builder", "construction", "developer", "broker", "agent", "homes", "apartments", "housing", "interior", "architecture"],
    },
    {
        "url": "https://sr-motors-oben-portfolio.vercel.app/",
        "tags": ["automotive", "motors", "car", "bike", "dealership", "auto", "showroom", "garage", "mechanic", "repair", "service center", "accessories", "vehicles"],
    },
    {
        "url": "https://smartfilesolutions.in/",
        "tags": ["business", "consulting", "ca", "accountant", "legal", "lawyer", "advocate", "tax", "finance", "filing", "agency", "corporate", "office", "services"],
    },
    {
        "url": "https://www.harmonystudio.co.in/",
        "tags": ["music", "dance", "studio", "yoga", "wellness", "spa", "beauty", "salon", "coaching", "school", "academy", "classes", "training", "art", "creative", "photography"],
    },
    {
        "url": "https://veeru-social-welfare-website.vercel.app/",
        "tags": ["ngo", "charity", "welfare", "social", "volunteer", "community", "trust", "foundation", "non profit", "society", "donation"],
    },
    {
        "url": "https://artsify.in/",
        "tags": ["art", "gallery", "portfolio", "creative", "design", "artist", "exhibition", "museum", "craft", "handmade"],
    },
    {
        "url": "https://www.tanisiimpex.com/",
        "tags": ["import", "export", "trading", "manufacturer", "wholesale", "supplier", "industrial", "logistics", "cargo", "b2b", "factory", "transport"],
    },
]


def _pick_portfolio_links(category: str) -> list[str]:
    """Pick the most relevant portfolio links first, then fill with others.
    Always returns at least 2 links so the lead sees enough work."""
    if not category:
        return [item["url"] for item in PORTFOLIO]

    cat_lower = category.lower()
    scored = []
    for item in PORTFOLIO:
        match_count = sum(1 for tag in item["tags"] if tag in cat_lower)
        scored.append((match_count, item["url"]))

    # Sort by relevance (highest match first), then add remaining
    scored.sort(key=lambda x: x[0], reverse=True)
    relevant = [url for count, url in scored if count > 0]
    others = [url for count, url in scored if count == 0]

    # Just show top relevant links (up to 2). If none match, show 1 fallback.
    if relevant:
        return relevant[:2]
    return others[:1]


# ── Few-shot examples so the AI learns the exact tone ──────────────────────────

WHATSAPP_EXAMPLE = """Hi bhai 👋

I checked out Trinity Fitness and noticed there's no website yet.

Here is a demo concept to see how it might look:
Demo:
https://premium-fitness-portfolio.vercel.app/

I can make a quick free demo for you too just to see how it looks. If you like it, we can build the full site. Let me know!"""

SMS_EXAMPLE = """Hi bhai 👋 Checked out Trinity Fitness and noticed no website yet. Here's a demo concept: https://premium-fitness-portfolio.vercel.app/ I can make a free demo for you too, if you like it we can build the full site. Let me know!"""

EMAIL_EXAMPLE_SUBJECT = "Quick homepage concept for Trinity Fitness"
EMAIL_EXAMPLE_BODY = """Hi bhai 👋,

I checked out Trinity Fitness and noticed there's no website yet.

Here is a demo concept to see how it might look:
Demo:
https://premium-fitness-portfolio.vercel.app/

I can make a quick free demo for you too just to see how it looks. If you like it, we can build the full site. Let me know!"""


# ── Main generation function ───────────────────────────────────────────────────

async def generate_outreach_message(
    name: str,
    category: str,
    rating: float | None,
    review_count: int | None,
    website_status: str,
    prompt_type: str = "initial",
    platform: str = "whatsapp",
) -> dict[str, str]:
    category_text = category or "business"

    if website_status == "NO_WEBSITE":
        context = "They do NOT have any website right now. Say: 'noticed there's no website yet'"
    elif website_status == "BROKEN":
        context = "They have a website but it is broken / not loading. Say: 'noticed the website wasn't loading'"
    else:
        context = "They have a working website but it could be much better. Say: 'noticed the current website could use an update'"

    portfolio_links = _pick_portfolio_links(category_text)
    demo_links_str = "\n".join(portfolio_links) if portfolio_links else "https://brijesh-dev-portfolio.vercel.app/"

    # ── Intent / follow-up context ──
    if prompt_type == "follow_up":
        intent_context = "You are sending a SHORT follow-up. They didn't reply to your first message. Keep it very short."
        cta_hint = "If you'd still like a free demo for your business, just let me know."
    elif prompt_type == "objection_budget":
        intent_context = "They said they don't have budget right now. Be extremely casual."
        cta_hint = "No worries! If you just want me to make a free demo for fun so you can see it, let me know."
    else:
        intent_context = "This is your FIRST message to them. You are showing them a demo concept."
        cta_hint = "I can make a quick free demo for you too. If you like it, we can build the full site. Let me know!"

    # ── System prompt for consistent persona ──
    system_prompt = """You are Vernora, a friendly Indian freelance web developer reaching out to local business owners.

TONE RULES (very important):
- Write like a real person texting. Extremely casual, warm, human.
- Start with "Hi bhai 👋" or "Hi 👋".
- Do NOT mention "Google". Just say "I checked out [Name]".
- Do NOT mention reviews, ratings, or stars.
- Do NOT talk about yourself ("I'm a web developer", "my past work", "my portfolio"). Make it about THEM.
- Do NOT use sales language ("online presence", "boost", "elevate", "stand out").
- Say "Here is a demo concept to see how it might look" before the links.
- End by offering: "I can make a quick free demo for you too just to see how it looks. If you like it, we can build the full site."
- ONLY include the provided Demo link(s). Format exactly as:
Demo:
[link 1]
[link 2 (if provided)]
- Keep it extremely short. 3-4 short lines max.

THINGS YOU MUST NEVER SAY:
- "I came across you on Google"
- "Saw your 4.5 star rating"
- "I'm a web developer"
- "Here is some of my past work"
- "Here is my portfolio"
- "Would you be open to"
- "I was playing around with some ideas" (Say "So I put together a quick homepage concept" instead)"""

    # ── Platform-specific user prompt ──
    if platform == "whatsapp":
        platform_rules = f"""WHATSAPP FORMAT:
- If their name is very long (like 'Trinity fitness lounge Gym best gym in miraroad'), SHORTEN IT naturally (e.g. 'Trinity Fitness').
- Keep the TOTAL message very short.
- Use 1-2 emojis max. Do NOT overdo it.

EXAMPLE of the tone and format I want (do NOT copy this exactly, just match the feel):
---
{WHATSAPP_EXAMPLE}
---"""
        json_format = '{\n  "whatsapp": "the whatsapp message"\n}'

    elif platform == "sms":
        platform_rules = f"""SMS FORMAT:
- Maximum 160 characters total. This is strict.
- NO emojis.

EXAMPLE:
---
{SMS_EXAMPLE}
---"""
        json_format = '{\n  "sms": "the sms message"\n}'

    else:  # email
        platform_rules = f"""EMAIL FORMAT:
- If their name is very long, SHORTEN IT naturally.
- Write a short, warm cold email that feels like a text message.
- Subject line must be simple and not clickbaity.
- NO emojis anywhere.

EXAMPLE:
Subject: {EMAIL_EXAMPLE_SUBJECT}
Body:
---
{EMAIL_EXAMPLE_BODY}
---"""
        json_format = '{\n  "email_subject": "subject line",\n  "email_body": "body of the email"\n}'

    user_prompt = f"""Write a {platform} outreach message for this business:

- Business Name: {name}
- Website situation: {context}

Context: {intent_context}
Call to action to use: {cta_hint}

Demo Link(s) to include:
{demo_links_str}

{platform_rules}

Return ONLY valid JSON, no extra text:
{json_format}"""

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.6,
        response_format={"type": "json_object"},
    )

    result = json.loads(response.choices[0].message.content)
    return {
        "whatsapp": result.get("whatsapp", ""),
        "sms": result.get("sms", ""),
        "email_subject": result.get("email_subject", ""),
        "email_body": result.get("email_body", ""),
    }
