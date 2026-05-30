from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
from services.website_service import check_website

router = APIRouter()


@router.post("/website", response_model=schemas.WebsiteCheckResult)
async def check_business_website(data: schemas.WebsiteCheckRequest):
    return await check_website(data.url)


@router.post("/business/{business_id}", response_model=schemas.BusinessOut)
async def check_and_update(business_id: int, db: Session = Depends(get_db)):
    business = db.query(models.Business).filter(models.Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    result = await check_website(business.website or "")
    business.website_status = result.status
    db.commit()
    db.refresh(business)
    return business
