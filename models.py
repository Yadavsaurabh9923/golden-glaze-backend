from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, CheckConstraint, func, Float
from sqlalchemy.orm import relationship
from database import Base # type: ignore
from pydantic import BaseModel, EmailStr

class Config(Base):
    __tablename__ = "configs"
    
    id = Column(Integer, primary_key=True, index=True)
    config_name = Column(String, unique=True, nullable=False)
    config_value = Column(String, nullable=False)
    timestamp = Column(DateTime, default=func.now(), onupdate=func.now())
    
class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(Integer, nullable=False)
    end_time = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    email = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=False)
    name = Column(String(255), nullable=False)
    status = Column(String(50), default="Pending")
    booking_time = Column(DateTime, default=func.now())
    date = Column(String(50), default=func.now())

    __table_args__ = (
        CheckConstraint("start_time >= 0 AND start_time <= 24", name="check_start_time"),
        CheckConstraint("end_time >= 0 AND end_time <= 24", name="check_end_time"),
    )
    
class BookingCreate(BaseModel):
    start_time: float
    end_time: float
    amount: float
    email: EmailStr
    phone_number: str
    name: str
    status: str = "Pending"
    date: str = datetime.now().strftime("%Y-%m-%d")

    class Config:
        from_attributes = True
    
class Rate(Base):
    __tablename__ = "rates"

    id = Column(Integer, primary_key=True, index=True)
    session = Column(String, nullable=False, unique=True)  # Unique to prevent duplicate sessions
    rate = Column(Float, nullable=False)
    last_changed = Column(DateTime, default=func.now(), onupdate=func.now()) 