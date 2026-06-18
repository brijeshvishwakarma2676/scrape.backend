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
# STRATEGY: Two-step outreach.
#   Step 1 (initial)  → a tiny simple-English question, NO links, NO pitch. Goal = just get a reply.
#   Step 2 (send_demo)→ only AFTER they reply, share the demo link inside the conversation.
# This beats the old "full pitch + link in message 1" which gave the owner the whole offer
# at once and left them nothing to reply to.

# Step 1 — the hook. One simple question. No links. No "I am a developer".
WHATSAPP_INITIAL_EXAMPLE = """Hello 😊 Is this Trinity Fitness?

I just wanted to ask you something quick."""

# Step 2 — sent after they reply. Now the demo link is welcome.
WHATSAPP_DEMO_EXAMPLE = """Great 🙌 I actually made a sample homepage design for you — totally free.

Takes 1 min to see 👇
https://premium-fitness-portfolio.vercel.app/

If you like it, we can build the full website. No pressure at all!"""

# Follow-up — they never replied to step 1. Tiny nudge, still a question.
WHATSAPP_FOLLOWUP_EXAMPLE = """Hi 😊 just checking — did you see my message?

I have a free design idea ready for your business. Want me to send it?"""

# Budget objection — reassure, no payment, just look.
WHATSAPP_BUDGET_EXAMPLE = """No problem at all 😊 You don't have to pay anything right now.

Let me just send you the free demo, you can take a look 👇
https://premium-fitness-portfolio.vercel.app/

If you like it we can think about it later, otherwise no worries!"""

SMS_EXAMPLE = """Hi! We made a free sample website design for Trinity Fitness. Want to see it? Reply and I will send the link."""

EMAIL_EXAMPLE_SUBJECT = "Quick website idea for Trinity Fitness"
EMAIL_EXAMPLE_BODY = """Hi,

I came across Trinity Fitness and put together a quick sample homepage design for you — completely free, just to show what's possible.

Here it is:
https://premium-fitness-portfolio.vercel.app/

If you like it, we can build the full website. No pressure at all — happy to hear your thoughts.

Thanks,
Vernora"""


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

    portfolio_links = _pick_portfolio_links(category_text)
    demo_links_str = "\n".join(portfolio_links) if portfolio_links else "https://brijesh-dev-portfolio.vercel.app/"

    # ── Decide whether THIS message should carry the demo link ──
    # WhatsApp first-touch (initial) and follow-up = NO link (just earn a reply first).
    # send_demo / objection_budget = link goes in. Email & SMS are one-shot, so link always goes in.
    is_whatsapp = platform == "whatsapp"
    include_links = (not is_whatsapp) or prompt_type in ("send_demo", "objection_budget")

    # ── Per-message-type intent + concrete example ──
    if prompt_type == "send_demo":
        intent_context = (
            "They REPLIED to your first message. Now share the free sample design. "
            "Sound happy they replied. Lead with the demo link, then offer to build the full site. No pressure."
        )
        wa_example = WHATSAPP_DEMO_EXAMPLE
    elif prompt_type == "follow_up":
        intent_context = (
            "They did NOT reply to your first message. Send a tiny, friendly nudge. "
            "Re-ask gently. Do NOT sound annoyed or pushy. Do NOT paste any link yet."
        )
        wa_example = WHATSAPP_FOLLOWUP_EXAMPLE
    elif prompt_type == "objection_budget":
        intent_context = (
            "They said they have no budget right now. Be very relaxed. Make clear there is ZERO payment "
            "needed to just look at the free demo. Share the link and tell them to decide later."
        )
        wa_example = WHATSAPP_BUDGET_EXAMPLE
    else:  # initial
        intent_context = (
            "This is your FIRST message. Your ONLY goal is to get a reply — nothing else. "
            "Ask ONE short, warm question (e.g. confirm they are the owner, or ask if they have a website). "
            "Do NOT pitch. Do NOT mention you make websites. Do NOT paste any link. Do NOT explain why you messaged."
        )
        wa_example = WHATSAPP_INITIAL_EXAMPLE

    # ── System prompt: the persona + hard rules ──
    system_prompt = """You are Vernora, a friendly freelance web developer messaging local business owners on WhatsApp.

Write in very SIMPLE, everyday English — the kind a local shop owner with basic English can read instantly. Warm, casual, human — like messaging a neighbourhood shop owner, not a corporate email.

HARD TONE RULES:
- NEVER start with "Hi bhai" — every spammer uses it and owners instantly ignore it. Start with "Hello 😊", "Hi 😊", or the business name.
- Use small, common words only. Short, plain sentences. No fancy or formal words.
- Make it feel 1-to-1 and personal. NEVER use words that hint it's a mass message: no "too", no "also", no "many businesses".
- Do NOT mention "Google", reviews, ratings, or stars.
- Do NOT use sales/agency language: no "online presence", "boost", "grow", "elevate", "stand out", "digital", "leverage".
- Use 1-2 emojis max. Never more.
- Extremely short. WhatsApp messages must be 1-3 short lines.

THINGS YOU MUST NEVER SAY:
- "Hi bhai"
- "I came across you on Google" / "Saw your rating"
- "I'm a web developer" (in the FIRST message)
- "Here is my portfolio" / "my past work"
- "Would you be open to" / "I'd love to discuss"
- Any sentence longer than 14 words."""

    # ── Platform-specific format block ──
    if is_whatsapp:
        if include_links:
            link_rule = f"""- Include the demo link(s) below, each on its own line, right after a line like "Takes 1 min to see 👇":
{demo_links_str}"""
        else:
            link_rule = "- Do NOT include ANY link or URL. This message's only job is to start a conversation."

        platform_rules = f"""WHATSAPP FORMAT:
- If the name is very long (e.g. 'Trinity fitness lounge Gym best gym in miraroad'), shorten it naturally (e.g. 'Trinity Fitness').
- Keep it to 1-3 short lines. Shorter = more replies.
- Use 1-2 emojis max.
{link_rule}

EXAMPLE of the exact tone/length I want (match the FEEL, do not copy word-for-word):
---
{wa_example}
---"""
        json_format = '{\n  "whatsapp": "the whatsapp message"\n}'

    elif platform == "sms":
        platform_rules = f"""SMS FORMAT:
- Maximum 160 characters total. This is strict.
- Very simple plain English. NO emojis.
- One sentence + a short question that invites a reply.
{f"- You may include this link: {demo_links_str.splitlines()[0]}" if include_links else "- NO links."}

EXAMPLE:
---
{SMS_EXAMPLE}
---"""
        json_format = '{\n  "sms": "the sms message"\n}'

    else:  # email
        platform_rules = f"""EMAIL FORMAT:
- Shorten a very long name naturally.
- Short, warm cold email in clean, simple English.
- Simple, non-clickbaity subject line.
- Include the demo link(s):
{demo_links_str}
- Sign off as "Vernora". NO emojis.

EXAMPLE:
Subject: {EMAIL_EXAMPLE_SUBJECT}
Body:
---
{EMAIL_EXAMPLE_BODY}
---"""
        json_format = '{\n  "email_subject": "subject line",\n  "email_body": "body of the email"\n}'

    user_prompt = f"""Write a {platform} outreach message for this business:

- Business Name: {name}
- Category: {category_text}

Situation: {intent_context}

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
