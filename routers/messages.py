from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
import json
from services.ai_service import generate_outreach_message

router = APIRouter()


@router.get("/{business_id}", response_model=list[schemas.MessageOut])
def get_messages(business_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.Message)
        .filter(models.Message.business_id == business_id)
        .order_by(models.Message.created_at.desc())
        .all()
    )


@router.post("", response_model=schemas.MessageOut, status_code=201)
async def generate_message(data: schemas.MessageCreate, db: Session = Depends(get_db)):
    business = db.query(models.Business).filter(models.Business.id == data.business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    messages = await generate_outreach_message(
        name=business.name,
        category=business.category or "business",
        rating=business.rating,
        review_count=business.review_count,
        website_status=business.website_status,
        prompt_type=data.prompt_type,
        platform=data.platform,
    )

    message = models.Message(
        business_id=business.id,
        generated_message=json.dumps(messages),
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message
