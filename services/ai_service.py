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
        "url": "https://www.tanisiimpex.com/",
        "tags": ["import", "export", "trading", "manufacturer", "wholesale", "supplier", "textile", "garment", "industrial", "logistics", "cargo", "shop", "store", "retail", "electronics", "b2b"],
    },
    {
        "url": "https://www.harmonystudio.co.in/",
        "tags": ["music", "dance", "studio", "fitness", "yoga", "gym", "wellness", "spa", "beauty", "salon", "coaching", "school", "academy", "classes", "training", "art", "craft", "creative"],
    },
    {
        "url": "https://premium-dining-restaurant.vercel.app/",
        "tags": ["restaurant", "food", "cafe", "dining", "bakery", "catering", "hotel", "bar", "lounge", "biryani", "pizza", "sweets", "juice", "kitchen", "dhaba", "tiffin"],
    },
    {
        "url": "https://premium-fitness-portfolio.vercel.app/",
        "tags": ["fitness", "gym", "workout", "crossfit", "sports", "martial arts", "boxing", "personal trainer", "health", "nutrition", "supplement", "physiotherapy", "rehab"],
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

    # Just show top 2 most relevant links, keeps it brief but gives enough examples
    result = relevant + others
    return result[:2]


def _build_rating_hook(rating: float | None) -> str:
    """Generate a very casual, short compliment based on rating."""
    if rating and rating >= 4.5:
        return f"Saw your {rating}⭐ rating on Google, great job! 👍"
    elif rating and rating >= 4.0:
        return f"Saw you're doing well on Google with {rating}⭐!"
    else:
        return ""


# ── Few-shot examples so the AI learns the exact tone ──────────────────────────

WHATSAPP_EXAMPLE = """Hi! 👋

I came across Royal Biryani on Google. Saw your 4.5⭐ rating, great job! 👍

I was playing around with some ideas and actually built a custom preview of what a new website for you could look like. 

Here is some of my past work:
- https://premium-dining-restaurant.vercel.app/
- https://www.tanisiimpex.com/
(Full portfolio: https://brijesh-dev-portfolio.vercel.app/)

Can I send over the preview link for you to see? No pressure!"""

SMS_EXAMPLE = """Hi! Came across Royal Biryani on Google. I make websites locally and put together a custom preview of a new site for you. Can I send the link?"""

EMAIL_EXAMPLE_SUBJECT = "Free website mockup for Royal Biryani"
EMAIL_EXAMPLE_BODY = """Hi there,

I came across Royal Biryani on Google. Saw your 4.5⭐ rating — great job!

I was playing around with some ideas and actually built a custom preview of what a new homepage for you could look like. I think it turned out really well.

Here's an example of my recent work:
- https://premium-dining-restaurant.vercel.app/
- https://www.harmonystudio.co.in/
(Full portfolio: https://brijesh-dev-portfolio.vercel.app/)

Would you be open to taking a quick look? Happy to send the link.

Thanks,
VernoraTech"""


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
        context = "They do NOT have any website right now."
    elif website_status == "BROKEN":
        context = "They have a website but it is broken / not loading."
    else:
        context = "They have a working website but it could be much better."

    portfolio_links = _pick_portfolio_links(category_text)
    portfolio_block = "\n".join(f"- {url}" for url in portfolio_links)

    rating_hook = _build_rating_hook(rating)

    # ── Intent / follow-up context ──
    if prompt_type == "follow_up":
        intent_context = "You are sending a SHORT follow-up. They didn't reply to your first message. Keep it very short — 2-3 lines max. Sound casual, not pushy."
        cta_hint = "Ask simply: 'Just checking if you saw my last message? I still have that free design ready if you want to take a look.'"
    elif prompt_type == "objection_budget":
        intent_context = "They said they don't have budget right now. Be extremely casual. Emphasize that it's just to LOOK, zero payment involved."
        cta_hint = "Ask simply: 'No worries at all! Can I just send the link so you can see it anyway? Completely free to look, no pressure.'"
    else:
        intent_context = "This is your FIRST message to them. You are introducing yourself casually."
        cta_hint = "End with a low-pressure question like: 'Is it okay if I send over the free design link for you to check out? No pressure at all.'"

    # ── System prompt for consistent persona ──
    system_prompt = """You are Vernora, a friendly Indian freelance web developer reaching out to local business owners on behalf of VernoraTech.

TONE RULES (very important):
- Write like you're texting a friend. Very casual, warm, human.
- Use simple everyday English that any Indian shop owner or small business person can instantly understand.
- Short sentences. 1-2 lines per paragraph max.
- Sound excited but NOT salesy. You genuinely want to help.
- NEVER sound like a marketing agency or corporate email.
- Use maximum 2-3 emojis (WhatsApp only). Zero emojis for email/SMS.

THINGS YOU MUST NEVER SAY:
- "I'm a web developer and I already made a quick free homepage design" (too scripted, say it naturally)
- "Completely free, no catch!" (sounds like a scam, say "no pressure at all")
- "I believe", "online presence", "connect with more clients"
- "enhance", "opportunities", "leverage", "boost"
- "digital presence", "maximize", "transform"
- "take your business to the next level"
- "stand out online", "drive more customers", "cutting-edge"
- "Would you be open to", "I'd love to discuss"
- "competitive edge", "unlock potential", "game-changer"
- "elevate", "empower", "streamline", "optimize"
- "value proposition", "synergy", "scalable"
- Any sentence longer than 15 words"""

    # ── Platform-specific user prompt ──
    if platform == "whatsapp":
        platform_rules = f"""WHATSAPP FORMAT:
- If their name is very long (like 'Trinity fitness lounge Gym best gym in miraroad'), SHORTEN IT naturally (e.g. 'Trinity Fitness').
- Start casually, e.g., "Hi! I was looking up places in the area and came across..."
{f'- Include this compliment naturally: {rating_hook}' if rating_hook else '- Do not mention ratings.'}
- Build curiosity: Say you were playing around with some ideas and actually built a custom preview of what a new site for them could look like.
- List the past work links under "Here is some of my past work:"
- Combine your main portfolio link concisely on the next line: "(Full portfolio: https://brijesh-dev-portfolio.vercel.app/)"
- {cta_hint}
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
- Start with "Hi!" and mention {name}.
- One simple sentence about what you do.
- End with a short question.
- NO links, NO emojis.

EXAMPLE:
---
{SMS_EXAMPLE}
---"""
        json_format = '{\n  "sms": "the sms message"\n}'

    else:  # email
        platform_rules = f"""EMAIL FORMAT:
- If their name is very long (like 'Trinity fitness lounge Gym best gym in miraroad'), SHORTEN IT naturally (e.g. 'Trinity Fitness').
- Write a short, warm cold email.
- Subject line must be simple and not clickbaity.
{f'- Include this compliment naturally: {rating_hook}' if rating_hook else '- Do not mention ratings.'}
- Build curiosity: Mention you were playing around with some ideas and built a custom preview of a new site for them.
- Include the past work links.
- Combine your main portfolio link concisely: "(Full portfolio: https://brijesh-dev-portfolio.vercel.app/)"
- Sign off as "VernoraTech".
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
- Category: {category_text}
- Website situation: {context}

Context: {intent_context}

Portfolio links to include (use ALL of these):
{portfolio_block}

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
