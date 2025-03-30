from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import re
import models, schemas # type: ignore
from database import engine, get_db # type: ignore
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum  # Import Mangum
from sqlalchemy import or_


models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS Settings (Add this middleware first)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

handler = Mangum(app) 

@app.get("/")
def read_root():
    return {"message": "Welcome to the API"}

# CONFIGS ENDPOINTS -------------------------------------------------------------------------------------

@app.get("/configs/", response_model=List[schemas.ConfigResponse])
def read_configs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    configs = db.query(models.Config).offset(skip).limit(limit).all()
    return [schemas.ConfigResponse.from_orm(config) for config in configs]

    return configs

@app.get("/configs/{config_id}", response_model=schemas.ConfigResponse)
def read_config(config_id: int, db: Session = Depends(get_db)):
    config = db.query(models.Config).filter(models.Config.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    return config

@app.get("/configs/by-name/{config_name}", response_model=schemas.ConfigResponse)
def read_config_by_name(config_name: str, db: Session = Depends(get_db)):
    config = db.query(models.Config).filter(models.Config.config_name == config_name).first()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    return config

@app.get("/update_config/{config_name}/{new_value}", response_model=schemas.ConfigResponse)
def update_config_by_name(config_name: str, new_value: str, db: Session = Depends(get_db)):
    config = db.query(models.Config).filter(models.Config.config_name == config_name).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    
    config.config_value = new_value
    db.commit()
    db.refresh(config)

    return config


# BOOKINGS ENDPOINTS -------------------------------------------------------------------------------------

@app.get("/get_all_bookings/", response_model=List[schemas.BookingResponse])
def read_bookings(skip: int = 0, limit: int = 10000, db: Session = Depends(get_db)):
    bookings = db.query(models.Booking).offset(skip).limit(limit).all()
    return bookings


@app.get("/booking/{phone_number}", response_model=List[schemas.BookingResponse])
def get_booking_by_phone(phone_number: str, db: Session = Depends(get_db)):
    bookings = db.query(models.Booking).filter(models.Booking.phone_number == phone_number).all()
    if not bookings:
        raise HTTPException(status_code=404, detail="Bookings not found")
    return [schemas.BookingResponse.from_orm(b) for b in bookings]




@app.post("/create_booking/", response_model=schemas.BookingResponse)
def create_booking(booking: models.BookingCreate, db: Session = Depends(get_db)):
    if not (0 <= booking.start_time <= 24 and 0 <= booking.end_time <= 24):
        raise HTTPException(
            status_code=400, 
            detail="Start time and end time must be between 0 and 24."
        )

    # Check if a booking already exists with the same date and
    # either the same start_time or end_time.
    existing_booking = db.query(models.Booking).filter(
        models.Booking.date == booking.date,
        or_(
            models.Booking.start_time == booking.start_time,
            models.Booking.end_time == booking.end_time
        )
    ).first()
    
    if existing_booking:
        raise HTTPException(
            status_code=400, 
            detail="A booking already exists with the same date and time."
        )

    new_booking = models.Booking(
        start_time=booking.start_time,
        end_time=booking.end_time,
        amount=booking.amount,
        email=booking.email,
        phone_number=booking.phone_number,
        name=booking.name,
        status="Hold",  # Force status to Hold
        date=booking.date,
        transaction_id=booking.transaction_id
    )
    
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    return new_booking

@app.post("/confirm_booking")
def confirm_booking(booking_request: schemas.ConfirmBookingRequest, db: Session = Depends(get_db)):
    booking = db.query(models.Booking).filter(
        models.Booking.id == booking_request.id
    ).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Check if any booking on the same date with status "Confirmed" exists that has either
    # the same start_time or the same end_time.
    conflict_booking = db.query(models.Booking).filter(
        models.Booking.date == booking.date,
        models.Booking.status == "Confirmed",
        or_(
            models.Booking.start_time == booking.start_time,
            models.Booking.end_time == booking.end_time
        )
    ).first()

    if conflict_booking:
        raise HTTPException(
            status_code=400, 
            detail="A booking already exists with the same date and time."
        )

    # Update status to Confirmed
    booking.status = "Confirmed"
    db.commit()
    db.refresh(booking)
    
    return booking


    booking = db.query(models.Booking).filter(models.Booking.id == booking_request.id).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Update status to Confirmed
    booking.status = "Confirmed"
    db.commit()
    db.refresh(booking)
    
    return booking

@app.post("/cancel_booking")
def cancel_booking(booking_data: schemas.BookingResponse, db: Session = Depends(get_db)):
    # Query for the booking using the id from the request body.
    booking = db.query(models.Booking).filter(models.Booking.id == booking_data.id).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status != "Hold":
        raise HTTPException(status_code=400, detail="Can only cancel bookings in Hold status")
    
    db.delete(booking)
    db.commit()
    return {"message": "Booking deleted successfully"}

# RATES ENDPOINTS -------------------------------------------------------------------------------------

@app.get("/rate/{session}", response_model=schemas.RateResponse)
def get_rate_by_session(session: str, db: Session = Depends(get_db)):
    rate = db.query(models.Rate).filter(models.Rate.session == session).first()
    
    if not rate:
        raise HTTPException(status_code=404, detail="Rate not found")
    
    return rate

@app.get("/rate/id/{rate_id}", response_model=schemas.RateResponse)
def get_rate_by_id(rate_id: int, db: Session = Depends(get_db)):
    rate = db.query(models.Rate).filter(models.Rate.id == rate_id).first()
    
    if not rate:
        raise HTTPException(status_code=404, detail="Rate not found")
    
    return rate

@app.get("/rates/", response_model=List[schemas.RateResponse])
def get_all_rates(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    rates = db.query(models.Rate).offset(skip).limit(limit).all()
    return rates

@app.get("/update_rate/session/{session}/{new_rate}", response_model=schemas.RateResponse)
def update_rate_by_session(session: str, new_rate: float, db: Session = Depends(get_db)):
    rate = db.query(models.Rate).filter(models.Rate.session == session).first()
    
    if not rate:
        raise HTTPException(status_code=404, detail="Rate not found for this session")
    
    rate.rate = new_rate
    db.commit()
    db.refresh(rate)

    return rate