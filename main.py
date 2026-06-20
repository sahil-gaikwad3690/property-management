"""
Property Rental Management System — FastAPI backend.

Run:  uvicorn main:app --reload
Open: http://127.0.0.1:8000
"""
import os
import shutil
import uuid
from typing import List

from fastapi import (
    FastAPI, Depends, HTTPException, status, UploadFile, File
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

import models
import schemas
from auth import (
    hash_password, verify_password, create_access_token, get_current_user
)
from database import Base, engine, get_db, SessionLocal

# ---- Paths ----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---- Create tables ----
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Property Rental Management System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded images and shared assets
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")


# =====================================================================
# AUTH
# =====================================================================
@app.post("/api/signup", response_model=schemas.Token)
def signup(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = models.User(
        full_name=payload.full_name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer", "user": user}


@app.post("/api/login", response_model=schemas.Token)
def login(payload: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer", "user": user}


@app.get("/api/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(get_current_user)):
    return current_user


# =====================================================================
# IMAGE UPLOAD
# =====================================================================
@app.post("/api/upload")
def upload_image(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
):
    allowed = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed:
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    fname = f"{uuid.uuid4().hex}{ext}"
    dest = os.path.join(UPLOAD_DIR, fname)
    with open(dest, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"image_url": f"/static/uploads/{fname}"}


# =====================================================================
# PROPERTY CRUD  (GET / POST / PUT / DELETE)
# =====================================================================
@app.get("/api/properties", response_model=List[schemas.PropertyOut])
def list_properties(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.Property)
        .filter(models.Property.owner_id == current_user.id)
        .order_by(models.Property.created_at.desc())
        .all()
    )


@app.get("/api/properties/{property_id}", response_model=schemas.PropertyOut)
def get_property(
    property_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    prop = _owned_property(property_id, db, current_user)
    return prop


@app.post("/api/properties", response_model=schemas.PropertyOut, status_code=201)
def create_property(
    payload: schemas.PropertyCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    prop = models.Property(owner_id=current_user.id, **payload.model_dump())
    db.add(prop)
    db.commit()
    db.refresh(prop)
    return prop


@app.put("/api/properties/{property_id}", response_model=schemas.PropertyOut)
def update_property(
    property_id: int,
    payload: schemas.PropertyUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    prop = _owned_property(property_id, db, current_user)
    for field, value in payload.model_dump().items():
        setattr(prop, field, value)
    db.commit()
    db.refresh(prop)
    return prop


@app.delete("/api/properties/{property_id}", status_code=204)
def delete_property(
    property_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    prop = _owned_property(property_id, db, current_user)
    db.delete(prop)
    db.commit()
    return None


def _owned_property(property_id: int, db: Session, user: models.User) -> models.Property:
    prop = (
        db.query(models.Property)
        .filter(models.Property.id == property_id, models.Property.owner_id == user.id)
        .first()
    )
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return prop


# =====================================================================
# MARKETPLACE  — browse properties listed for sale (any owner)
# =====================================================================
@app.get("/api/marketplace", response_model=List[schemas.PropertyOut])
def marketplace(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Properties that are for sale, excluding the current user's own."""
    return (
        db.query(models.Property)
        .filter(
            models.Property.listing_type.in_(["Sale", "Both"]),
            models.Property.status != "Sold",
            models.Property.owner_id != current_user.id,
        )
        .order_by(models.Property.created_at.desc())
        .all()
    )


# =====================================================================
# INQUIRIES  — a buyer expresses interest / makes an offer on a sale
# =====================================================================
def _inquiry_out(inq: models.Inquiry) -> dict:
    """Flatten an inquiry plus its property/buyer details for the response."""
    return {
        "id": inq.id,
        "property_id": inq.property_id,
        "buyer_id": inq.buyer_id,
        "message": inq.message,
        "offer_amount": inq.offer_amount,
        "status": inq.status,
        "created_at": inq.created_at,
        "property_title": inq.property.title if inq.property else "",
        "property_city": inq.property.city if inq.property else "",
        "buyer_name": inq.buyer.full_name if inq.buyer else "",
    }

@app.post(
    "/api/properties/{property_id}/inquiries",
    response_model=schemas.InquiryOut,
    status_code=201,
)
def create_inquiry(
    property_id: int,
    payload: schemas.InquiryCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    prop = db.query(models.Property).filter(models.Property.id == property_id).first()
    if not prop or prop.listing_type not in ("Sale", "Both"):
        raise HTTPException(status_code=404, detail="Property not available for sale")
    if prop.owner_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot inquire on your own property")
    inquiry = models.Inquiry(
        property_id=property_id,
        buyer_id=current_user.id,
        message=payload.message,
        offer_amount=payload.offer_amount,
    )
    db.add(inquiry)
    db.commit()
    db.refresh(inquiry)
    return _inquiry_out(inquiry)


@app.get("/api/inquiries/received", response_model=List[schemas.InquiryOut])
def inquiries_received(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Inquiries other buyers sent on the current user's properties."""
    rows = (
        db.query(models.Inquiry)
        .join(models.Property, models.Inquiry.property_id == models.Property.id)
        .filter(models.Property.owner_id == current_user.id)
        .order_by(models.Inquiry.created_at.desc())
        .all()
    )
    return [_inquiry_out(i) for i in rows]


@app.get("/api/inquiries/sent", response_model=List[schemas.InquiryOut])
def inquiries_sent(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Inquiries the current user has sent as a buyer."""
    rows = (
        db.query(models.Inquiry)
        .filter(models.Inquiry.buyer_id == current_user.id)
        .order_by(models.Inquiry.created_at.desc())
        .all()
    )
    return [_inquiry_out(i) for i in rows]


@app.put("/api/inquiries/{inquiry_id}", response_model=schemas.InquiryOut)
def respond_inquiry(
    inquiry_id: int,
    new_status: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Owner accepts or declines an inquiry on one of their properties."""
    if new_status not in ("Accepted", "Declined"):
        raise HTTPException(status_code=400, detail="status must be Accepted or Declined")
    inquiry = (
        db.query(models.Inquiry)
        .join(models.Property, models.Inquiry.property_id == models.Property.id)
        .filter(
            models.Inquiry.id == inquiry_id,
            models.Property.owner_id == current_user.id,
        )
        .first()
    )
    if not inquiry:
        raise HTTPException(status_code=404, detail="Inquiry not found")
    inquiry.status = new_status
    if new_status == "Accepted":
        inquiry.property.status = "Sold"
    db.commit()
    db.refresh(inquiry)
    return _inquiry_out(inquiry)


# =====================================================================
# FRONTEND PAGES
# =====================================================================
def _page(name: str) -> FileResponse:
    return FileResponse(os.path.join(FRONTEND_DIR, name))


@app.get("/")
def page_root():
    return _page("login.html")


@app.get("/login")
def page_login():
    return _page("login.html")


@app.get("/signup")
def page_signup():
    return _page("signup.html")


@app.get("/dashboard")
def page_dashboard():
    return _page("index.html")


@app.get("/create")
def page_create():
    return _page("create.html")


@app.get("/update")
def page_update():
    return _page("update.html")


@app.get("/marketplace")
def page_marketplace():
    return _page("marketplace.html")


@app.get("/inquiries")
def page_inquiries():
    return _page("inquiries.html")


# =====================================================================
# DEMO SEED  — gives a logged-out visitor something nice to look at.
# Login:  demo@rental.app  /  demo1234
# =====================================================================
def seed_demo():
    db = SessionLocal()
    try:
        if db.query(models.User).filter(models.User.email == "demo@rental.app").first():
            return
        user = models.User(
            full_name="Demo Owner",
            email="demo@rental.app",
            hashed_password=hash_password("demo1234"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        samples = [
            dict(title="Skyline Loft 12B", address="221 Marine Drive", city="Mumbai",
                 type="Apartment", bedrooms=2, bathrooms=2, area_sqft=1100,
                 rent_amount=58000, status="Rented", tenant_name="Aarav Mehta",
                 description="Sea-facing loft with floor-to-ceiling windows and a private balcony.",
                 image_url="https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=900&q=80"),
            dict(title="Garden Villa 7", address="14 Koregaon Park Lane", city="Pune",
                 type="Villa", bedrooms=4, bathrooms=3, area_sqft=2800,
                 rent_amount=95000, status="Available", tenant_name="",
                 listing_type="Sale", sale_price=42000000,
                 description="Spacious villa with a landscaped garden and covered parking for two cars.",
                 image_url="https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=900&q=80"),
            dict(title="Studio 04 — The Hive", address="9 Brigade Road", city="Bengaluru",
                 type="Studio", bedrooms=1, bathrooms=1, area_sqft=480,
                 rent_amount=24000, status="Available", tenant_name="",
                 description="Compact, light-filled studio steps from cafes and the metro.",
                 image_url="https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=900&q=80"),
            dict(title="Riverside House", address="3 Boat Club Road", city="Pune",
                 type="House", bedrooms=3, bathrooms=2, area_sqft=1900,
                 rent_amount=72000, status="Available", tenant_name="",
                 listing_type="Both", sale_price=28500000,
                 description="Quiet riverside home currently undergoing a kitchen refit.",
                 image_url="https://images.unsplash.com/photo-1570129477492-45c003edd2be?w=900&q=80"),
        ]
        for s in samples:
            db.add(models.Property(owner_id=user.id, **s))
        db.commit()
    finally:
        db.close()


seed_demo()
