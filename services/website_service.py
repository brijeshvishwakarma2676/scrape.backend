import httpx
from urllib.parse import urlparse
from schemas import WebsiteCheckResult

SOCIAL_MEDIA_DOMAINS = {
    "instagram.com",
    "facebook.com",
    "fb.com",
    "twitter.com",
    "x.com",
    "linkedin.com",
    "youtube.com",
    "youtu.be",
    "tiktok.com",
    "snapchat.com",
    "pinterest.com",
    "threads.net",
    "t.me",
    "wa.me",
    "linktr.ee",
    "linktree.com",
    "g.co",
    "maps.google.com",
    "goo.gl",
}


async def check_website(url: str) -> WebsiteCheckResult:
    if not url or url.strip() == "":
        return WebsiteCheckResult(status="NO_WEBSITE", detail="No URL provided")

    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    parsed = urlparse(url)
    domain = parsed.netloc.lower().removeprefix("www.")
    if any(domain == s or domain.endswith(f".{s}") for s in SOCIAL_MEDIA_DOMAINS):
        return WebsiteCheckResult(status="NO_WEBSITE", detail=f"Social media / directory link ({domain})")

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(url)
            if response.status_code < 400:
                return WebsiteCheckResult(status="WORKING", detail=f"HTTP {response.status_code}")
            else:
                return WebsiteCheckResult(status="BROKEN", detail=f"HTTP {response.status_code}")
    except httpx.TimeoutException:
        return WebsiteCheckResult(status="BROKEN", detail="Timeout after 10s")
    except httpx.ConnectError:
        return WebsiteCheckResult(status="BROKEN", detail="Connection refused")
    except Exception as e:
        return WebsiteCheckResult(status="BROKEN", detail=str(e)[:100])
