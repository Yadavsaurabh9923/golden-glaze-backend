from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class ConfigResponse(BaseModel):
    id: int
    config_name: str
    config_value: str
    timestamp: Optional[datetime]

    class Config:
        from_attributes = True  # Updated from orm_mode=True

class BookingResponse(BaseModel):
    id: int
    start_time: int
    end_time: int
    amount: float
    email: str
    phone_number: str
    name: str
    status: str
    booking_time: Optional[datetime]

    class Config:
        from_attributes = True  # Updated
        
class RateBase(BaseModel):
    session: str
    rate: float
    
class RateResponse(RateBase):
    id: int
    last_changed: datetime

    class Config:
        from_attributes = True  # Updated
        
class RateUpdate(BaseModel):
    rate: float