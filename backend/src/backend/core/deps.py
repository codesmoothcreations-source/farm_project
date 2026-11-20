# (get_db, get_current_user, require_role)
from sqlalchemy.orm import Session
from .database import SessionLocal

 
def get_db():
    db: Session = SessionLocal
    try:
        yield db
    finally:
        db.close()