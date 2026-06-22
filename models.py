"""ORM models. Each property belongs to the owner (logged-in user)."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    # Nullable: users who sign in with Google have no local password.
    hashed_password = Column(String, nullable=True)
    google_id = Column(String, unique=True, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    properties = relationship(
        "Property", back_populates="owner", cascade="all, delete-orphan"
    )
    inquiries = relationship(
        "Inquiry", back_populates="buyer", cascade="all, delete-orphan"
    )


class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    address = Column(String, nullable=False)
    city = Column(String, nullable=False)
    type = Column(String, default="Apartment")      # Apartment / House / Studio / Villa
    bedrooms = Column(Integer, default=1)
    bathrooms = Column(Integer, default=1)
    area_sqft = Column(Integer, default=0)
    listing_type = Column(String, default="Rent")     # Rent / Sale / Both
    rent_amount = Column(Float, default=0)
    sale_price = Column(Float, default=0)
    status = Column(String, default="Available")     # Available / Rented / Sold / Maintenance
    tenant_name = Column(String, default="")
    description = Column(Text, default="")
    image_url = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="properties")
    inquiries = relationship(
        "Inquiry", back_populates="property", cascade="all, delete-orphan"
    )


class Inquiry(Base):
    """A purchase inquiry/offer a buyer sends to a property's owner."""
    __tablename__ = "inquiries"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, default="")
    offer_amount = Column(Float, default=0)
    status = Column(String, default="Pending")        # Pending / Accepted / Declined
    created_at = Column(DateTime, default=datetime.utcnow)

    property = relationship("Property", back_populates="inquiries")
    buyer = relationship("User", back_populates="inquiries")
