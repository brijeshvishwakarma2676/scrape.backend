import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
import models
from services.website_service import check_website
from services.ai_service import generate_outreach_message

router = APIRouter()


class BulkProcessRequest(BaseModel):
    business_ids: list[int]


class BulkProcessResult(BaseModel):
    websites_checked: int
    messages_generated: int
    errors: int


@router.post("/bulk", response_model=BulkProcessResult)
async def bulk_process(request: BulkProcessRequest, db: Session = Depends(get_db)):
    if not request.business_ids:
        raise HTTPException(status_code=400, detail="No business IDs provided")

    businesses = db.query(models.Business).filter(
        models.Business.id.in_(request.business_ids)
    ).all()

    # Step 1: Check all websites concurrently (max 5 at a time)
    sem = asyncio.Semaphore(5)

    async def check_one(b: models.Business):
        async with sem:
            result = await check_website(b.website or "")
            return b.id, result.status

    check_results = await asyncio.gather(*[check_one(b) for b in businesses])

    status_map = dict(check_results)
    for b in businesses:
        b.website_status = status_map.get(b.id, b.website_status)
    db.commit()
    db.expire_all()

    # Reload with fresh website_status
    businesses = db.query(models.Business).filter(
        models.Business.id.in_(request.business_ids)
    ).all()

    # Step 2: Generate messages sequentially (avoid rate limits)
    generated = 0
    errors = 0
    for b in businesses:
        try:
            msgs = await generate_outreach_message(
                name=b.name,
                category=b.category or "business",
                rating=b.rating,
                review_count=b.review_count,
                website_status=b.website_status,
            )
            db.add(models.Message(
                business_id=b.id,
                generated_message=json.dumps(msgs),
            ))
            generated += 1
        except Exception:
            errors += 1

    db.commit()

    return BulkProcessResult(
        websites_checked=len(businesses),
        messages_generated=generated,
        errors=errors,
    )
