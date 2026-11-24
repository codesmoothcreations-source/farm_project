farmconnect/backend/
│
├── alembic/                   # DB Migrations (critical for team collaboration)
├── alembic.ini
├── .env
├── pyproject.toml             # or requirements.txt
├── main.py                    # FastAPI app initialization, mounts all routers
│
└── src/
    ├── core/                  # ⚙️ SHARED INFRASTRUCTURE (No business logic here)
    │   ├── config.py          # Settings (Pydantic BaseSettings)
    │   ├── database.py        # SQLAlchemy engine, SessionLocal, Base
    │   ├── security.py        # JWT creation/verification, Password hashing
    │   ├── deps.py            # Shared dependencies (get_db, get_current_user, RoleCheckers)
    │   ├── exceptions.py      # Custom app exceptions (e.g., NotFoundError, AuthError)
    │   ├── enums.py           # ALL Python Enums (UserRole, OrderStatus, etc.)
    │   └── registry.py        # Imports all models so Alembic can see them
    │
    ├── shared/                # 🧩 SHARED BUSINESS LOGIC
    │   ├── models.py          # Tables shared across features (e.g., users, regions, crops)
    │   ├── schemas.py         # Shared Pydantic models (e.g., pagination, basic user response)
    │   └── services/          # e.g., EmailService, CloudinaryService, PaystackService
    │
    ├── auth/                  # 🔐 AUTHENTICATION (Login, OTP, Reset)
    │   ├── models.py          # user_credentials, refresh_tokens, otp_codes
    │   ├── schemas.py         # LoginRequest, TokenResponse, OTPVerify
    │   ├── service.py         # Hash password, verify OTP, rotate refresh token
    │   ├── router.py          # /api/v1/auth/login, /register, /reset-password
    │   └── dependencies.py    # get_current_active_user (role-aware)
    │
    ├── users/                 # 👤 USER PROFILES & PHONES
    │   ├── models.py          # user_phones
    │   ├── schemas.py         # PhoneCreate, UserProfileUpdate
    │   ├── service.py         # Add phone, change primary phone
    │   └── router.py          # /api/v1/users/me, /users/me/phones
    │
    ├── farmers/               # 🚜 FARMER DOMAIN
    │   ├── models.py          # farmer_profiles, farms
    │   ├── schemas.py         # FarmerProfileCreate, FarmUpdate
    │   ├── service.py         # Submit verification, manage farms
    │   └── router.py          # /api/v1/farmers, /api/v1/farms
    │
    ├── buyers/                # 🛒 BUYER DOMAIN
    │   ├── models.py          # buyer_profiles, saved_listings
    │   ├── schemas.py         # BuyerProfileCreate
    │   ├── service.py         # Update buyer type, toggle saved listings
    │   └── router.py          # /api/v1/buyers, /api/v1/saved-listings
    │
    ├── transporters/          # 🚚 TRANSPORTER DOMAIN
    │   ├── models.py          # transporter_profiles
    │   ├── schemas.py         # VehicleUpdate, RegionUpdate
    │   ├── service.py         # Manage vehicle, update operating regions
    │   └── router.py          # /api/v1/transporters
    │
    ├── listings/              # 🌾 SUPPLY (Listings, Crops, Images)
    │   ├── models.py          # listings, listing_images
    │   ├── schemas.py         # ListingCreate, ListingResponse
    │   ├── service.py         # Search, filter, update stock, image upload
    │   └── router.py          # /api/v1/listings
    │
    ├── livestreams/           # 📺 LIVE STREAMING (Cloudinary)
    │   ├── models.py          # livestreams, livestream_comments, viewer_sessions
    │   ├── schemas.py         # StreamCreate, CommentCreate
    │   ├── service.py         # Generate Cloudinary token, handle webhooks
    │   └── router.py          # /api/v1/livestreams, /webhooks/cloudinary
    │
    ├── enquiries/             # 💬 CHAT & NEGOTIATION
    │   ├── models.py          # enquiries, enquiry_messages
    │   ├── schemas.py         # EnquiryCreate, MessageCreate
    │   ├── service.py         # Create thread, send message, update status
    │   └── router.py          # /api/v1/enquiries
    │
    ├── orders/                # 📦 COMMERCE (Checkout, Status)
    │   ├── models.py          # orders, order_status_history
    │   ├── schemas.py         # OrderCreate, OrderStatusUpdate
    │   ├── service.py         # Calculate totals, transition states, snapshots
    │   └── router.py          # /api/v1/orders
    │
    ├── payments/              # 💰 MONEY (Paystack, Payouts, Webhooks)
    │   ├── models.py          # payments, payouts, webhook_events
    │   ├── schemas.py         # PaymentInit, WebhookPayload
    │   ├── service.py         # Init Paystack, handle webhooks, trigger payouts
    │   └── router.py          # /api/v1/payments, /webhooks/paystack
    │
    └── admin/                 # 🛡️ BACKOFFICE (Moderation, Audit)
        ├── models.py          # audit_logs
        ├── schemas.py         # AdminAction
        ├── service.py         # Verify farmer, suspend user, view metrics
        └── router.py          # /api/v1/admin