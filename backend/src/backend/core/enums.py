from enum import Enum

class UserRole(Enum):
    FARMER: str = "farmer"
    BUYER: str = "buyer"
    TRANSPORTER: str = "transporter"
    ADMIN: str = "admin"


class UserStatus(Enum):
    ACTIVE: str = "active"
    SUSPENDED: str = "suspended"
    DEACTIVATED: str = "deactivated"

# I will add the rest of the enums here as 
class VerificationStatus(Enum):
    UNVERIFIED: str = 'unverified'
    PENDING: str = 'pending'
    VERIFIED: str = 'verified'
    REJECTED: str = 'rejected'


class BuyerType(Enum):
    INDIVIDUAL: str = 'individual'
    TRADER: str = 'trader'
    RESTAURANT: str = 'restaurant'
    PROCESSOR: str = 'processor'
    RETAILER: str = 'retailer'
    OTHER: str = 'other'


class Vehicle_type(Enum):
    MOTORBICKE: str = 'motorbicke'
    TRICYCLE: str = 'tricycle'
    PICKUP: str = 'pickup'
    SMALL_TRACK: str = 'small_track'
    MEDIUM_TRACK: str = 'medium_track'
    LARGE_TRACK: str = 'large_track'
    REFIGERATED_TRACK: str = 'refigerated_track'


class MomoNetwork(Enum):
    MTN: str = 'mtn'
    TELECEL: str = 'telecel'
    AIRTELTIGO: str = 'airteltigo'