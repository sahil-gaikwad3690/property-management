"""Pydantic schemas (request bodies + response models)."""
from datetime import datetime
from pydantic import BaseModel, EmailStr


# ---------- Auth ----------
class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class GoogleAuth(BaseModel):
    # The ID token ("credential") returned by Google Identity Services.
    credential: str


class UserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Property ----------
class PropertyBase(BaseModel):
    title: str
    address: str
    city: str
    type: str = "Apartment"
    bedrooms: int = 1
    bathrooms: int = 1
    area_sqft: int = 0
    listing_type: str = "Rent"      # Rent / Sale / Both
    rent_amount: float = 0
    sale_price: float = 0
    status: str = "Available"
    tenant_name: str = ""
    description: str = ""
    image_url: str = ""


class PropertyCreate(PropertyBase):
    pass


class PropertyUpdate(PropertyBase):
    pass


class PropertyOut(PropertyBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True


# ---------- Inquiry (buyer interest in a property for sale) ----------
class InquiryCreate(BaseModel):
    message: str = ""
    offer_amount: float = 0


class InquiryOut(BaseModel):
    id: int
    property_id: int
    buyer_id: int
    message: str
    offer_amount: float
    status: str
    created_at: datetime
    property_title: str = ""
    property_city: str = ""
    buyer_name: str = ""

    class Config:
        from_attributes = True
