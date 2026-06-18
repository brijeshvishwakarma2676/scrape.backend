import httpx
import os
from dotenv import load_dotenv
from services.phone_utils import classify_phone

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")


async def search_places(query: str, max_results: int = 20) -> list[dict]:
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_PLACES_API_KEY is not set in .env")

    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "X-Goog-Api-Key": GOOGLE_API_KEY,
        "X-Goog-FieldMask": (
            "places.displayName,"
            "places.formattedAddress,"
            "places.rating,"
            "places.userRatingCount,"
            "places.websiteUri,"
            "places.nationalPhoneNumber,"
            "places.primaryTypeDisplayName"
        ),
        "Content-Type": "application/json",
    }
    body = {
        "textQuery": query,
        "maxResultCount": min(max_results, 20),
        "languageCode": "en",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(url, json=body, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    results = []
    for place in data.get("places", []):
        website = place.get("websiteUri")
        phone = place.get("nationalPhoneNumber")
        results.append({
            "name": place.get("displayName", {}).get("text", "Unknown"),
            "category": place.get("primaryTypeDisplayName", {}).get("text") if place.get("primaryTypeDisplayName") else None,
            "phone": phone,
            "phone_type": classify_phone(phone),
            "website": website,
            "address": place.get("formattedAddress"),
            "rating": place.get("rating"),
            "review_count": place.get("userRatingCount", 0),
            "website_status": "UNCHECKED" if website else "NO_WEBSITE",
        })

    return results
