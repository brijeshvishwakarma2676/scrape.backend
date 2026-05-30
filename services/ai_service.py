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
) -> dict[str, str]:
    rating_text = f"{rating} stars with {review_count} reviews" if rating else "no rating info available"
    category_text = category or "business"

    if website_status == "NO_WEBSITE":
        context = "They do not currently have a website."
        whatsapp_hint = "Hi! I came across your business and noticed you don't currently have a website."
        sms_hint = "Hi! I noticed your business doesn't have a website."
    elif website_status == "BROKEN":
        context = "They have a website but it is not working properly."
        whatsapp_hint = "Hi! I visited your website and noticed it isn't loading properly."
        sms_hint = "Hi! Your website seems to have an issue - it isn't loading."
    else:
        context = "They have a working website with room for improvement."
        whatsapp_hint = "Hi! I visited your website and found a few opportunities to improve the design and user experience."
        sms_hint = "Hi! I checked your website and think there are ways to improve it."

    portfolio_links = _pick_portfolio_links(category_text)
    portfolio_block = "\n".join(f"- {url}" for url in portfolio_links)

    prompt = f"""You are a freelancer texting a local business owner on WhatsApp. Write exactly like a real person — not like ChatGPT, not like a sales email, not like marketing copy.

Business details:
- Name: {name}
- Category: {category_text}
- Rating: {rating_text}
- Website situation: {context}

Portfolio links (include ALL of these in the WhatsApp message):
{portfolio_block}

---

GOOD EXAMPLE (copy this tone and structure exactly):

Hi!

I came across 24/7 Fitness Club and noticed you have 122 reviews. 💪

I couldn't find a website for the gym.

A lot of people check online before joining, so I thought I'd reach out.

Some recent websites I've worked on:
https://www.harmonystudio.co.in/

Would you like to see a quick demo idea for your gym?

---

WHATSAPP RULES:
- Start exactly: "Hi!\\n\\nI came across {name}..."
- Mention ONE specific thing: their rating, review count, or the website problem. Not all of them.
- Short sentences. Line breaks between thoughts. Like a real text.
- Sound like a person, not a company.
- Talk about one problem only. Do not list multiple issues.
- Include ALL portfolio links under "Some recent websites I've worked on:" — each on its own line.
- End with a short question. Examples: "Interested?", "Can I show you?", "Want to see it?", "Would you like a quick demo?"
- 60-120 words total.

BANNED WORDS AND PHRASES — never use any of these:
I believe, online presence, connect with more clients, opportunities, enhance, improve your business, would you be open to, I'd love to discuss, leverage, boost, enhance your online presence, digital presence, maximize growth, transform your business, take your business to the next level, stand out online, drive more customers, professional online presence, cutting-edge, clearly has a great reputation, I noticed some opportunities

---

SMS RULES:
- Start: "Hi! I came across {name}..."
- 1-2 sentences max. Under 160 characters.
- No links.
- End with a short question.

---

Return ONLY this JSON, no extra text:
{{
  "whatsapp": "the whatsapp message",
  "sms": "the sms message"
}}"""

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
    }
