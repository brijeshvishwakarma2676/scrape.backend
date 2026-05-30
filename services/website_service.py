import httpx
from schemas import WebsiteCheckResult


async def check_website(url: str) -> WebsiteCheckResult:
    if not url or url.strip() == "":
        return WebsiteCheckResult(status="NO_WEBSITE", detail="No URL provided")

    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

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
