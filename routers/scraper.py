from fastapi import APIRouter, Query, HTTPException
from services.scraper_service import search_places

router = APIRouter()


@router.get("/search")
async def scrape_search(
    q: str = Query(..., description="e.g. restaurants in Koramangala Bangalore"),
    max: int = Query(20, ge=1, le=20),
):
    try:
        return await search_places(q, max)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Google Places API error: {str(e)[:200]}")
