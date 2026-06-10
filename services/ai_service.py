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

    # Always show at least 2: relevant first, fill with others
    result = relevant + others
    return result[:4]  # cap at 4 max


def _build_rating_hook(name: str, rating: float | None, review_count: int | None) -> str:
    """Generate a natural compliment line based on the business rating."""
    if rating and rating >= 4.5 and review_count and review_count >= 20:
        return f"{name} has amazing reviews — {rating}⭐ with {review_count}+ reviews! Customers clearly love it."
    elif rating and rating >= 4.0:
        return f"{name} is doing great with {rating}⭐ rating. That's solid!"
    elif rating and rating >= 3.0:
        return f"{name} is already getting customers coming in."
    else:
        return ""


# ── Few-shot examples so the AI learns the exact tone ──────────────────────────

WHATSAPP_EXAMPLE = """Hi! 👋

I came across Royal Biryani House on Google and I really liked it — 4.5⭐ with 200+ reviews! 🔥

I'm a web developer and I already made a quick free homepage design for Royal Biryani House. Just to show you how it can look.

Some websites I have made:
- https://www.tanisiimpex.com/
- https://premium-dining-restaurant.vercel.app/

You can also see my full portfolio here: https://brijesh-dev-portfolio.vercel.app/

Can I send you the free design link to check it out? Completely free, no catch!"""

SMS_EXAMPLE = """Hi! I saw Royal Biryani House on Google — great reviews! I make websites for local businesses. Can I show you a free design I made for you?"""

EMAIL_EXAMPLE_SUBJECT = "I made a free website design for Royal Biryani House"
EMAIL_EXAMPLE_BODY = """Hi,

I came across Royal Biryani House on Google and really liked your 4.5⭐ rating!

I'm a web developer and I already made a quick, free homepage design just for your business. No cost, no commitment — I just want to show you how it could look.

Here are some websites I have built:
- https://www.tanisiimpex.com/
- https://www.harmonystudio.co.in/

You can also view my complete portfolio at: https://brijesh-dev-portfolio.vercel.app/

Would you like to see the free design? Happy to share the link.

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

    rating_hook = _build_rating_hook(name, rating, review_count)

    # ── Intent / follow-up context ──
    if prompt_type == "follow_up":
        intent_context = "You are sending a SHORT follow-up. They didn't reply to your first message. Keep it very short — 3-4 lines max. Sound casual, not pushy."
        cta_hint = "Ask simply: 'Did you get a chance to see my message? I still have that free design ready for you.'"
    elif prompt_type == "objection_budget":
        intent_context = "They said they don't have budget right now. Be understanding. Remind them it is 100% free to just LOOK at the design. No payment needed."
        cta_hint = "Ask simply: 'Can I just send you the link to see? No payment needed at all, just have a look.'"
    else:
        intent_context = "This is your FIRST message to them. You are introducing yourself."
        cta_hint = "End with: 'Can I send you the free design link to check it out? (Completely free, no catch!)'"

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
- Start with a casual greeting and mention you found {name} on Google.
{f'- Include this compliment naturally: {rating_hook}' if rating_hook else '- Do not mention ratings since we have no data.'}
- Say you already made a quick, free, custom homepage design for {name}.
- List portfolio links under "Some websites I have made:" — each on its own line.
- Always mention your main portfolio link naturally (e.g. "Or see all my work here: https://brijesh-dev-portfolio.vercel.app/").
- {cta_hint}
- Keep the TOTAL message under 120 words.
- Use 2-3 emojis only. Do NOT overuse emojis.

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
- Write a short, warm cold email (under 100 words for body).
- Subject line must be specific to {name} — catchy but simple.
{f'- Include this compliment naturally: {rating_hook}' if rating_hook else '- Do not mention ratings since we have no data.'}
- Mention the free mockup offer.
- Include portfolio links.
- Always include your main portfolio link: https://brijesh-dev-portfolio.vercel.app/
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
