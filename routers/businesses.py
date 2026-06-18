from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from database import get_db
import models
import schemas
from services.phone_utils import classify_phone

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


@router.get("/analytics", response_model=schemas.Analytics)
def get_analytics(db: Session = Depends(get_db)):
    B = models.Business

    def grouped(column, labels: dict[str, str] | None = None, order: list[str] | None = None):
        rows = dict(db.query(column, func.count(B.id)).group_by(column).all())
        keys = order or sorted(rows.keys(), key=lambda k: -rows[k])
        out = []
        for k in keys:
            count = rows.get(k, 0)
            if count == 0 and order is None:
                continue
            name = labels.get(k, k) if labels else (k or "Unknown")
            out.append(schemas.NameValue(name=name, value=count))
        return out

    # ── Leads over time (daily new + running cumulative) ──
    date_rows = (
        db.query(func.date(B.created_at), func.count(B.id))
        .group_by(func.date(B.created_at))
        .order_by(func.date(B.created_at))
        .all()
    )
    leads_over_time = []
    cumulative = 0
    for d, c in date_rows:
        cumulative += c
        leads_over_time.append(
            schemas.TimePoint(date=str(d), new=c, cumulative=cumulative)
        )

    # ── Status breakdowns ──
    lead_status = grouped(
        B.lead_status,
        order=["NEW", "CONTACTED", "INTERESTED", "WON", "LOST"],
    )
    website_status = grouped(
        B.website_status,
        labels={
            "NO_WEBSITE": "No Website",
            "WORKING": "Working",
            "BROKEN": "Broken",
            "UNCHECKED": "Unchecked",
        },
        order=["NO_WEBSITE", "WORKING", "BROKEN", "UNCHECKED"],
    )
    phone_type = grouped(
        B.phone_type,
        labels={"mobile": "Mobile", "landline": "Landline", "unknown": "Unknown"},
        order=["mobile", "landline", "unknown"],
    )

    # ── Top categories (skip empty) ──
    cat_rows = (
        db.query(B.category, func.count(B.id))
        .filter(B.category.isnot(None), B.category != "")
        .group_by(B.category)
        .order_by(func.count(B.id).desc())
        .limit(6)
        .all()
    )
    top_categories = [schemas.NameValue(name=c, value=n) for c, n in cat_rows]

    # ── Conversion funnel (monotonic) ──
    total = db.query(func.count(B.id)).scalar() or 0
    contacted = db.query(func.count(B.id)).filter(
        B.lead_status.in_(["CONTACTED", "INTERESTED", "WON"])
    ).scalar() or 0
    interested = db.query(func.count(B.id)).filter(
        B.lead_status.in_(["INTERESTED", "WON"])
    ).scalar() or 0
    won = db.query(func.count(B.id)).filter(B.lead_status == "WON").scalar() or 0
    funnel = [
        schemas.NameValue(name="Total Leads", value=total),
        schemas.NameValue(name="Contacted", value=contacted),
        schemas.NameValue(name="Interested", value=interested),
        schemas.NameValue(name="Won", value=won),
    ]

    messages_sent = db.query(func.count(models.Message.id)).scalar() or 0

    return schemas.Analytics(
        leads_over_time=leads_over_time,
        lead_status=lead_status,
        website_status=website_status,
        phone_type=phone_type,
        top_categories=top_categories,
        funnel=funnel,
        messages_sent=messages_sent,
    )


@router.get("", response_model=schemas.PaginatedBusinessOut)
def list_businesses(
    search: Optional[str] = Query(None),
    lead_status: Optional[str] = Query(None),
    website_status: Optional[str] = Query(None),
    phone_type: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None),
    sort_dir: Optional[str] = Query("desc"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=0),
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
    if phone_type:
        q = q.filter(models.Business.phone_type == phone_type)

    total = q.count()

    sort_col = {
        "name": models.Business.name,
        "rating": models.Business.rating,
        "review_count": models.Business.review_count,
        "created_at": models.Business.created_at,
    }.get(sort_by, models.Business.created_at)
    q = q.order_by(sort_col.asc() if sort_dir == "asc" else sort_col.desc())

    if limit > 0:
        offset = (page - 1) * limit
        items = q.offset(offset).limit(limit).all()
        pages = (total + limit - 1) // limit
    else:
        items = q.all()
        pages = 1
        limit = total

    return schemas.PaginatedBusinessOut(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


@router.post("/bulk-delete", status_code=204)
def bulk_delete_businesses(body: schemas.BulkIds, db: Session = Depends(get_db)):
    if body.ids:
        db.query(models.Business).filter(models.Business.id.in_(body.ids)).delete(synchronize_session=False)
        db.commit()


@router.post("/bulk-status")
def bulk_update_status(body: schemas.BulkStatus, db: Session = Depends(get_db)):
    if body.ids:
        db.query(models.Business).filter(models.Business.id.in_(body.ids)).update(
            {models.Business.lead_status: body.status}, synchronize_session=False
        )
        db.commit()
    return {"updated": len(body.ids)}


@router.post("", response_model=schemas.BusinessOut, status_code=201)
def create_business(data: schemas.BusinessCreate, db: Session = Depends(get_db)):
    business = models.Business(**data.model_dump())
    if not business.website or business.website.strip() == "":
        business.website_status = "NO_WEBSITE"
    business.phone_type = classify_phone(business.phone)
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
    update_data = data.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(business, field, value)
    if "phone" in update_data:
        business.phone_type = classify_phone(business.phone)
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
