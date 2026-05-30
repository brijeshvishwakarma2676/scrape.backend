from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from database import get_db
import models
import schemas

router = APIRouter()


@router.get("/stats", response_model=schemas.DashboardStats)
def get_stats(db: Session = Depends(get_db)):
    total = db.query(func.count(models.Business.id)).scalar()
    no_website = db.query(func.count(models.Business.id)).filter(
        models.Business.website_status == "NO_WEBSITE"
    ).scalar()
    broken = db.query(func.count(models.Business.id)).filter(
        models.Business.website_status == "BROKEN"
    ).scalar()
    contacted = db.query(func.count(models.Business.id)).filter(
        models.Business.lead_status == "CONTACTED"
    ).scalar()
    interested = db.query(func.count(models.Business.id)).filter(
        models.Business.lead_status == "INTERESTED"
    ).scalar()
    won = db.query(func.count(models.Business.id)).filter(
        models.Business.lead_status == "WON"
    ).scalar()
    return schemas.DashboardStats(
        total=total,
        no_website=no_website,
        broken_website=broken,
        contacted=contacted,
        interested=interested,
        won=won,
    )


@router.get("", response_model=list[schemas.BusinessOut])
def list_businesses(
    search: Optional[str] = Query(None),
    lead_status: Optional[str] = Query(None),
    website_status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(models.Business)
    if search:
        q = q.filter(
            models.Business.name.ilike(f"%{search}%")
            | models.Business.category.ilike(f"%{search}%")
            | models.Business.address.ilike(f"%{search}%")
        )
    if lead_status:
        q = q.filter(models.Business.lead_status == lead_status)
    if website_status:
        q = q.filter(models.Business.website_status == website_status)
    return q.order_by(models.Business.created_at.desc()).all()


@router.post("", response_model=schemas.BusinessOut, status_code=201)
def create_business(data: schemas.BusinessCreate, db: Session = Depends(get_db)):
    business = models.Business(**data.model_dump())
    if not business.website or business.website.strip() == "":
        business.website_status = "NO_WEBSITE"
    db.add(business)
    db.commit()
    db.refresh(business)
    return business


@router.get("/{business_id}", response_model=schemas.BusinessOut)
def get_business(business_id: int, db: Session = Depends(get_db)):
    business = db.query(models.Business).filter(models.Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    return business


@router.put("/{business_id}", response_model=schemas.BusinessOut)
def update_business(business_id: int, data: schemas.BusinessUpdate, db: Session = Depends(get_db)):
    business = db.query(models.Business).filter(models.Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(business, field, value)
    db.commit()
    db.refresh(business)
    return business


@router.delete("/{business_id}", status_code=204)
def delete_business(business_id: int, db: Session = Depends(get_db)):
    business = db.query(models.Business).filter(models.Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    db.delete(business)
    db.commit()
