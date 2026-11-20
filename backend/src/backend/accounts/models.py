from datetime import datetime
# 
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Numeric, DateTime, func
# 
from ..core.database import Base

# (Region)
class Region(Base):
    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(primary_key=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)


# (User)
class User(Base):
    __tablename__ = "users"
    
    # pass for now
    pass