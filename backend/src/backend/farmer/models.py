from datetime import datetime
# 
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Numeric, Enum, DateTime, func
# 
from ..core.database import Base


# (FarmerProfile)
class FarmerProfile(Base):
    __tablename__ = "farmer_profiles"

    # fields upcomming