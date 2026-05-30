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
        "url": "https://www.artsify.in/",
        "tags": ["art", "craft", "gallery", "creative", "design", "decor", "studio", "artist", "handmade", "print"],
    },
    {
        "url": "https://www.harmonystudio.co.in/",
        "tags": ["music", "dance", "studio", "fitness", "yoga", "gym", "wellness", "spa", "beauty", "salon", "coaching", "school", "academy", "classes", "training"],
    },
    {
        "url": "https://www.tanisiimpex.com/",
        "tags": ["import", "export", "trading", "manufacturer", "wholesale", "supplier", "textile", "garment", "industrial", "logistics", "cargo", "shop", "store", "retail", "electronics"],
    },
    {
        "url": "https://babaproperties.vercel.app/",
        "tags": ["property", "real estate", "realty", "housing", "builder", "construction", "architect", "interior", "home", "apartment", "plot", "land", "rental"],
    },
]


def _pick_portfolio_links(_category: str) -> list[str]:
    return [item["url"] for item in PORTFOLIO]


async def generate_outreach_message(
    name: str,
    category: str,
    rating: float | None,
    review_count: int | None,
    website_status: str,
    prompt_type: str = "initial",
    platform: str = "whatsapp",
) -> dict[str, str]:
    rating_text = f"{rating} stars with {review_count} reviews" if rating else "no rating info available"
    category_text = category or "business"

    if website_status == "NO_WEBSITE":
        context = "They do not currently have a website."
    elif website_status == "BROKEN":
        context = "They have a website but it is not working properly."
    else:
        context = "They have a working website with room for improvement."

    portfolio_links = _pick_portfolio_links(category_text)
    portfolio_block = "\n".join(f"- {url}" for url in portfolio_links)

    # Contextual rules based on the prompt type
    if prompt_type == "follow_up":
        intent_context = "You are sending a short follow-up message to remind them."
        whatsapp_start = "Hi! Just checking if you saw my previous message."
        whatsapp_end = "Do you want to see the free design I made for you? It's completely free."
    elif prompt_type == "objection_budget":
        intent_context = "They replied saying they don't have money right now. Assure them it is free to look."
        whatsapp_start = "I completely understand! Budget is tight for everyone right now."
        whatsapp_end = "Can I just show you the design anyway? No pressure to buy, I just want you to see it."
    else:
        intent_context = "This is your first time reaching out to them."
        whatsapp_start = f"Hi!\n\nI came across {name}..."
        whatsapp_end = "Can I send you the free design link to check it out? (Completely free, no catch!)"

    # Define platform-specific rules and JSON format
    platform_rules = ""
    json_format = ""
    
    if platform == "whatsapp":
        platform_rules = f"""WHATSAPP RULES:
- Start with something like: "{whatsapp_start}"
- Tell them you have already made a quick, free, custom homepage design for their business ({name}) to show them.
- Include ALL portfolio links under "Some websites I have made:" — each on its own line.
- End with a simple question: "{whatsapp_end}"
- Use 2-3 emojis maximum.
- VERY IMPORTANT: Write in extremely simple, basic English. It must be instantly understandable by a local Indian shop owner or small business person. Do not use heavy vocabulary. Keep sentences very short."""
        json_format = '{\n  "whatsapp": "the whatsapp message"\n}'
        
    elif platform == "sms":
        platform_rules = f"""SMS RULES:
- Start: "Hi! I came across {name}..."
- 1-2 sentences max. Under 160 characters.
- No links.
- End with a short simple question.
- VERY IMPORTANT: Write in extremely simple, basic English for a local Indian business owner."""
        json_format = '{\n  "sms": "the sms message"\n}'
        
    else:  # email
        platform_rules = f"""EMAIL RULES:
- Write a short cold email with the exact same free mockup offer.
- Keep it highly personalized, professional but very simple.
- Provide a catchy, simple subject line.
- Include ALL portfolio links.
- VERY IMPORTANT: Write in extremely simple, basic English. It must be instantly understandable by a local Indian shop owner. No complex corporate words."""
        json_format = '{\n  "email_subject": "subject line for the email",\n  "email_body": "body of the email"\n}'

    prompt = f"""You are a freelancer contacting a local Indian business owner. 
Write exactly like a real person sending a normal message.

Business details:
- Name: {name}
- Category: {category_text}
- Rating: {rating_text}
- Website situation: {context}

Context: {intent_context}

Portfolio links (include ALL of these if requested):
{portfolio_block}

---

{platform_rules}

BANNED WORDS AND PHRASES — never use any of these:
I believe, online presence, connect with more clients, opportunities, enhance, improve your business, would you be open to, I'd love to discuss, leverage, boost, digital presence, maximize growth, transform, take your business to the next level, stand out online, drive more customers, cutting-edge

---

Return ONLY this JSON, no extra text:
{json_format}"""

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        response_format={"type": "json_object"},
    )

    result = json.loads(response.choices[0].message.content)
    return {
        "whatsapp": result.get("whatsapp", ""),
        "sms": result.get("sms", ""),
        "email_subject": result.get("email_subject", ""),
        "email_body": result.get("email_body", ""),
    }
