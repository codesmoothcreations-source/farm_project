-- ═══════════════════════════════════════════════════════════════════════
-- ENUMS — must exist before any table references them
-- ═══════════════════════════════════════════════════════════════════════

-- ── Identity ──────────────────────────────────────────────────────────
CREATE TYPE user_role AS ENUM ('farmer', 'buyer', 'transporter', 'admin');
CREATE TYPE user_status AS ENUM ('active', 'suspended', 'deactivated');
CREATE TYPE verification_status AS ENUM ('unverified', 'pending', 'verified', 'rejected');

-- ── Phones & payments ─────────────────────────────────────────────────
CREATE TYPE phone_type AS ENUM ('primary', 'secondary', 'momo_payout');
CREATE TYPE momo_network AS ENUM ('mtn', 'telecel', 'airteltigo');

-- ── Buyer profile ─────────────────────────────────────────────────────
CREATE TYPE buyer_type AS ENUM ('individual', 'trader', 'restaurant', 'processor', 'retailer', 'other');

-- ── Transporter profile ───────────────────────────────────────────────
CREATE TYPE vehicle_type AS ENUM (
  'motorbike', 'tricycle', 'pickup',
  'small_truck', 'medium_truck', 'large_truck', 'refrigerated_truck'
);

-- ── Crops & produce ───────────────────────────────────────────────────
CREATE TYPE crop_category AS ENUM (
  'cereal', 'legume', 'tuber', 'vegetable', 'fruit',
  'cash_crop', 'spice', 'livestock', 'poultry', 'other'
);
CREATE TYPE quality_grade AS ENUM ('ungraded', 'grade_a', 'grade_b', 'grade_c', 'mixed');
CREATE TYPE quantity_unit AS ENUM ('kg', 'g', 'tonne', 'bag_50kg', 'bag_100kg', 'crate', 'basket', 'piece', 'bundle', 'bunch');
CREATE TYPE delivery_method AS ENUM ('pickup', 'farmer_delivery', 'transporter');

-- ── Listing lifecycle ─────────────────────────────────────────────────
CREATE TYPE listing_status AS ENUM ('draft', 'active', 'paused', 'sold_out', 'expired', 'removed');

-- ── Enquiry lifecycle ─────────────────────────────────────────────────
CREATE TYPE enquiry_status AS ENUM ('open', 'replied', 'accepted', 'declined', 'closed');

-- ── Order lifecycle ───────────────────────────────────────────────────
CREATE TYPE order_status AS ENUM (
  'pending', 'accepted', 'rejected',
  'in_transit', 'delivered', 'completed',
  'cancelled', 'disputed'
);

-- ── Money ─────────────────────────────────────────────────────────────
CREATE TYPE payment_status AS ENUM ('initiated', 'pending', 'success', 'failed', 'refunded');
CREATE TYPE payout_status  AS ENUM ('pending', 'processing', 'paid', 'failed', 'cancelled');

-- ── Notifications ─────────────────────────────────────────────────────
CREATE TYPE notification_channel AS ENUM ('in_app', 'email', 'sms', 'push');

-- ── OTP ───────────────────────────────────────────────────────────────
CREATE TYPE otp_purpose AS ENUM ('verify_email', 'verify_phone', 'two_factor');

-- ── Livestream ────────────────────────────────────────────────────────
CREATE TYPE livestream_status AS ENUM ('scheduled', 'live', 'ended', 'cancelled', 'failed');









-- ═══════════════════════════════════════════════════════════════════════
-- REGIONS
-- ═══════════════════════════════════════════════════════════════════════
CREATE TABLE regions (
  id          SMALLSERIAL PRIMARY KEY,
  name        TEXT NOT NULL UNIQUE,                        -- "Greater Accra"
  slug        TEXT NOT NULL UNIQUE,                        -- "greater-accra" — URL-safe
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ═══════════════════════════════════════════════════════════════════════
-- CROPS — canonical crop list, referenced by listings
-- ═══════════════════════════════════════════════════════════════════════
CREATE TABLE crops (
  id          SMALLSERIAL PRIMARY KEY,
  slug        TEXT NOT NULL UNIQUE,                        -- "maize", "tomato"
  name        TEXT NOT NULL,                               -- "Maize"
  category    crop_category NOT NULL,
  is_active   BOOLEAN NOT NULL DEFAULT TRUE,               -- soft-delete: keep history, hide from pickers
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX crops_category_active_idx ON crops (category) WHERE is_active = TRUE;













-- ═══════════════════════════════════════════════════════════════════════
-- USERS — identity only. No password, no phone. Those live elsewhere.
-- ═══════════════════════════════════════════════════════════════════════
CREATE TABLE users (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  role               user_role NOT NULL,                        -- fixed at signup; role data lives in *_profiles
  full_name          TEXT NOT NULL,
  email              TEXT NOT NULL,                             -- PRIMARY login identifier
  email_verified_at  TIMESTAMPTZ,                               -- NULL = unverified; gate features on this
  status             user_status NOT NULL DEFAULT 'active',     -- checked on EVERY authenticated request
  preferred_lang     TEXT NOT NULL DEFAULT 'en',
  region_id          SMALLINT REFERENCES regions(id) ON DELETE SET NULL,
  avatar_url         TEXT,
  last_login_at      TIMESTAMPTZ,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Case-insensitive email uniqueness — "A@x.com" and "a@x.com" are the same account
CREATE UNIQUE INDEX users_email_lower_uniq ON users (lower(email));
CREATE INDEX users_role_status_idx ON users (role, status);
CREATE INDEX users_region_idx      ON users (region_id) WHERE region_id IS NOT NULL;

-- ═══════════════════════════════════════════════════════════════════════
-- USER_CREDENTIALS — password + token versioning. 1:1 with users.
-- ═══════════════════════════════════════════════════════════════════════
CREATE TABLE user_credentials (
  user_id               UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  password_hash         TEXT NOT NULL,                          -- Argon2id or bcrypt — never plaintext
  password_changed_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  token_version         INTEGER NOT NULL DEFAULT 0,             -- bump to invalidate ALL issued JWTs (logout everywhere)
  failed_login_count    SMALLINT NOT NULL DEFAULT 0,
  last_failed_login_at  TIMESTAMPTZ,
  locked_until          TIMESTAMPTZ,                            -- login rejected while > now()
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ═══════════════════════════════════════════════════════════════════════
-- USER_PHONES — all phone numbers, typed. A user can have many.
-- ═══════════════════════════════════════════════════════════════════════
CREATE TABLE user_phones (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  phone        TEXT NOT NULL,                                   -- E.164 only, e.g. +233241234567
  phone_type   phone_type NOT NULL,
  label        TEXT,                                            -- "home", "office", "mother's farm"
  network      momo_network,                                    -- required for momo_payout; NULL otherwise
  verified_at  TIMESTAMPTZ,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT phone_e164 CHECK (phone ~ '^\+[1-9][0-9]{7,14}$'),
  CONSTRAINT momo_network_required CHECK (
    (phone_type =  'momo_payout' AND network IS NOT NULL) OR
    (phone_type <> 'momo_payout' AND network IS NULL)
  )
);

CREATE UNIQUE INDEX user_phones_phone_uniq      ON user_phones (phone);                          -- one phone → one user (anti-fraud)
CREATE UNIQUE INDEX user_phones_one_primary     ON user_phones (user_id) WHERE phone_type = 'primary';
CREATE UNIQUE INDEX user_phones_one_momo_payout ON user_phones (user_id) WHERE phone_type = 'momo_payout';
CREATE INDEX        user_phones_user_idx        ON user_phones (user_id);

-- ═══════════════════════════════════════════════════════════════════════
-- OTP_CODES — short-lived codes delivered via EMAIL only.
-- ═══════════════════════════════════════════════════════════════════════
CREATE TABLE otp_codes (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email         TEXT NOT NULL,                                   -- lowercased target email
  code_hash     TEXT NOT NULL,                                   -- SHA-256 of the 6-digit code
  purpose       otp_purpose NOT NULL,
  attempts      SMALLINT NOT NULL DEFAULT 0,
  max_attempts  SMALLINT NOT NULL DEFAULT 5,
  expires_at    TIMESTAMPTZ NOT NULL,
  consumed_at   TIMESTAMPTZ,
  requested_ip  INET,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX otp_codes_active_idx  ON otp_codes (email, purpose) WHERE consumed_at IS NULL;
CREATE INDEX otp_codes_cleanup_idx ON otp_codes (expires_at)     WHERE consumed_at IS NULL;

-- ═══════════════════════════════════════════════════════════════════════
-- PASSWORD_RESET_TOKENS — 32-byte URL tokens emailed to the user.
-- Only the SHA-256 hash is stored; the raw token is in the URL.
-- ═══════════════════════════════════════════════════════════════════════
CREATE TABLE password_reset_tokens (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token_hash    TEXT NOT NULL UNIQUE,
  expires_at    TIMESTAMPTZ NOT NULL,                            -- now() + INTERVAL '30 min'
  consumed_at   TIMESTAMPTZ,
  requested_ip  INET,
  user_agent    TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX password_reset_tokens_user_idx    ON password_reset_tokens (user_id)    WHERE consumed_at IS NULL;
CREATE INDEX password_reset_tokens_cleanup_idx ON password_reset_tokens (expires_at) WHERE consumed_at IS NULL;

-- ═══════════════════════════════════════════════════════════════════════
-- REFRESH_TOKENS — rotating refresh-token family, one row per rotation.
-- ═══════════════════════════════════════════════════════════════════════
CREATE TABLE refresh_tokens (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token_hash   TEXT NOT NULL UNIQUE,
  expires_at   TIMESTAMPTZ NOT NULL,
  revoked_at   TIMESTAMPTZ,
  replaced_by  UUID REFERENCES refresh_tokens(id),               -- next token in rotation chain
  user_agent   TEXT,
  ip           INET,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX refresh_tokens_user_active_idx ON refresh_tokens (user_id)     WHERE revoked_at IS NULL;
CREATE INDEX refresh_tokens_expires_idx     ON refresh_tokens (expires_at);
CREATE INDEX refresh_tokens_family_idx      ON refresh_tokens (replaced_by) WHERE replaced_by IS NOT NULL;










-- ═══════════════════════════════════════════════════════════════════════
-- FARMER_PROFILES — 1:1 with users (role='farmer')
-- momo payout info now lives in user_phones (phone_type='momo_payout')
-- ═══════════════════════════════════════════════════════════════════════
CREATE TABLE farmer_profiles (
  user_id              UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  business_name        TEXT,
  bio                  TEXT,
  years_farming        SMALLINT CHECK (years_farming >= 0),
  verification_status  verification_status NOT NULL DEFAULT 'unverified',
  verified_at          TIMESTAMPTZ,
  ghana_card_doc_key   TEXT,                                     -- private storage key — NEVER expose publicly
  rating_avg           NUMERIC(3,2) NOT NULL DEFAULT 0 CHECK (rating_avg BETWEEN 0 AND 5),
  rating_count         INTEGER NOT NULL DEFAULT 0 CHECK (rating_count >= 0),
  created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX farmer_profiles_verified_idx ON farmer_profiles (verification_status) WHERE verification_status = 'verified';

-- ═══════════════════════════════════════════════════════════════════════
-- BUYER_PROFILES — 1:1 with users (role='buyer')
-- ═══════════════════════════════════════════════════════════════════════
CREATE TABLE buyer_profiles (
  user_id           UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  business_name     TEXT,
  buyer_type        buyer_type,
  delivery_address  TEXT,
  lat               NUMERIC(9,6) CHECK (lat BETWEEN -90 AND 90),
  lng               NUMERIC(9,6) CHECK (lng BETWEEN -180 AND 180),
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ═══════════════════════════════════════════════════════════════════════
-- TRANSPORTER_PROFILES — 1:1 with users (role='transporter')
-- ═══════════════════════════════════════════════════════════════════════
CREATE TABLE transporter_profiles (
  user_id              UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  company_name         TEXT,
  vehicle_type         vehicle_type NOT NULL,
  vehicle_plate        TEXT,
  capacity_kg          INTEGER CHECK (capacity_kg > 0),
  operating_region_ids SMALLINT[] NOT NULL DEFAULT '{}',         -- array of regions.id
  verification_status  verification_status NOT NULL DEFAULT 'unverified',
  verified_at          TIMESTAMPTZ,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX transporter_profiles_regions_gin ON transporter_profiles USING GIN (operating_region_ids);










-- ═══════════════════════════════════════════════════════════════════════
-- FARMS — physical locations owned by farmers
-- ═══════════════════════════════════════════════════════════════════════
CREATE TABLE farms (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name             TEXT NOT NULL,
  region_id        SMALLINT NOT NULL REFERENCES regions(id),
  district         TEXT,
  town             TEXT,
  address_text     TEXT,
  lat              NUMERIC(9,6) CHECK (lat BETWEEN -90 AND 90),
  lng              NUMERIC(9,6) CHECK (lng BETWEEN -180 AND 180),
  google_place_id  TEXT,
  size_acres       NUMERIC(10,2) CHECK (size_acres > 0),
  is_active        BOOLEAN NOT NULL DEFAULT TRUE,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX farms_owner_idx  ON farms (owner_id)  WHERE is_active = TRUE;
CREATE INDEX farms_region_idx ON farms (region_id) WHERE is_active = TRUE;

-- ═══════════════════════════════════════════════════════════════════════
-- LISTINGS — what farmers are selling
-- ═══════════════════════════════════════════════════════════════════════
CREATE TABLE listings (
  id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  farmer_id              UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  farm_id                UUID NOT NULL REFERENCES farms(id) ON DELETE RESTRICT,
  crop_id                SMALLINT NOT NULL REFERENCES crops(id),
  region_id              SMALLINT NOT NULL REFERENCES regions(id),   -- denormalized from farm for fast filtering
  title                  TEXT NOT NULL,
  description            TEXT,
  variety                TEXT,                                       -- "Obatanpa", "Jasmine"
  quality_grade          quality_grade NOT NULL DEFAULT 'ungraded',
  is_organic             BOOLEAN NOT NULL DEFAULT FALSE,
  unit                   quantity_unit NOT NULL,
  unit_weight_kg         NUMERIC(8,2) CHECK (unit_weight_kg > 0),    -- e.g. 1 bag_50kg = 50
  price_per_unit_pesewas BIGINT NOT NULL CHECK (price_per_unit_pesewas > 0),
  price_negotiable       BOOLEAN NOT NULL DEFAULT TRUE,
  quantity_available     NUMERIC(12,2) NOT NULL CHECK (quantity_available >= 0),
  min_order_quantity     NUMERIC(12,2) NOT NULL DEFAULT 1 CHECK (min_order_quantity > 0),
  harvest_date           DATE,
  available_from         DATE,
  available_until        DATE,
  delivery_options       delivery_method[] NOT NULL DEFAULT '{pickup}',
  status                 listing_status NOT NULL DEFAULT 'draft',
  view_count             INTEGER NOT NULL DEFAULT 0,
  search_vector          TSVECTOR,                                   -- populated by trigger; used for full-text search
  created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT min_le_available CHECK (
    min_order_quantity <= quantity_available
    OR status IN ('draft','sold_out','expired','removed')
  )
);

CREATE INDEX listings_farmer_idx     ON listings (farmer_id, status);
CREATE INDEX listings_browse_idx     ON listings (status, region_id, crop_id, created_at DESC) WHERE status = 'active';
CREATE INDEX listings_crop_idx       ON listings (crop_id)   WHERE status = 'active';
CREATE INDEX listings_region_idx     ON listings (region_id) WHERE status = 'active';
CREATE INDEX listings_search_gin     ON listings USING GIN (search_vector)   WHERE status = 'active';
CREATE INDEX listings_delivery_gin   ON listings USING GIN (delivery_options) WHERE status = 'active';

-- ═══════════════════════════════════════════════════════════════════════
-- LISTING_IMAGES — one-to-many photos, ordered by position
-- ═══════════════════════════════════════════════════════════════════════
CREATE TABLE listing_images (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  listing_id  UUID NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
  storage_key TEXT NOT NULL,                                       -- Cloudinary public_id or S3 key
  position    SMALLINT NOT NULL DEFAULT 0,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX listing_images_listing_idx ON listing_images (listing_id, position);

-- ═══════════════════════════════════════════════════════════════════════
-- SAVED_LISTINGS — buyer's wishlist
-- ═══════════════════════════════════════════════════════════════════════
CREATE TABLE saved_listings (
  user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  listing_id UUID NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, listing_id)
);

CREATE INDEX saved_listings_listing_idx ON saved_listings (listing_id);








-- ═══════════════════════════════════════════════════════════════════════
-- LIVESTREAMS — one row per stream. Cloudinary owns the media; we own
-- the metadata + analytics. Optionally attached to a farm and/or listing.
-- ═══════════════════════════════════════════════════════════════════════
CREATE TABLE livestreams (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  farmer_id          UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  farm_id            UUID REFERENCES farms(id)    ON DELETE SET NULL,   -- optional
  listing_id         UUID REFERENCES listings(id) ON DELETE SET NULL,   -- optional — "selling this in the stream"
  title              TEXT NOT NULL,
  description        TEXT,
  scheduled_for      TIMESTAMPTZ,                                       -- planned start time
  started_at         TIMESTAMPTZ,                                       -- actual start
  ended_at           TIMESTAMPTZ,                                       -- actual end
  status             livestream_status NOT NULL DEFAULT 'scheduled',
  provider           TEXT NOT NULL DEFAULT 'cloudinary',
  provider_stream_id TEXT,                                              -- Cloudinary's unique stream id
  playback_url_hls   TEXT,                                              -- HLS manifest (.m3u8)
  playback_url_mp4   TEXT,                                              -- fallback MP4
  thumbnail_url      TEXT,
  peak_viewers       INTEGER NOT NULL DEFAULT 0,                        -- max concurrent viewers
  total_viewers      INTEGER NOT NULL DEFAULT 0,                        -- unique viewers
  total_watch_seconds BIGINT NOT NULL DEFAULT 0,                        -- sum of watch time
  duration_seconds   INTEGER,                                           -- computed on end
  cancelled_reason   TEXT,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX livestreams_farmer_idx     ON livestreams (farmer_id, status);
CREATE INDEX livestreams_status_idx     ON livestreams (status, scheduled_for);
CREATE INDEX livestreams_listing_idx    ON livestreams (listing_id) WHERE listing_id IS NOT NULL;
CREATE INDEX livestreams_live_idx       ON livestreams (started_at DESC) WHERE status = 'live';

-- ═══════════════════════════════════════════════════════════════════════
-- LIVESTREAM_RECORDINGS — resulting video files (for storage billing + replay)
-- ═══════════════════════════════════════════════════════════════════════
CREATE TABLE livestream_recordings (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  livestream_id     UUID NOT NULL REFERENCES livestreams(id) ON DELETE CASCADE,
  provider_public_id TEXT NOT NULL,
  format            TEXT NOT NULL,                                    -- 'mp4', 'hls', 'dash'
  resolution        TEXT,                                             -- '1080p', '720p', 'audio_only'
  size_bytes        BIGINT NOT NULL DEFAULT 0,                        -- for storage cost tracking
  duration_seconds  INTEGER,
  storage_url       TEXT NOT NULL,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX livestream_recordings_stream_idx ON livestream_recordings (livestream_id);

-- ═══════════════════════════════════════════════════════════════════════
-- LIVESTREAM_VIEWER_SESSIONS — one row per viewer join; analytics source
-- ═══════════════════════════════════════════════════════════════════════
CREATE TABLE livestream_viewer_sessions (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  livestream_id  UUID NOT NULL REFERENCES livestreams(id) ON DELETE CASCADE,
  user_id        UUID REFERENCES users(id) ON DELETE SET NULL,        -- NULL = anonymous viewer
  session_token  TEXT,                                                -- anonymous viewer fingerprint (cookie-based)
  joined_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  left_at        TIMESTAMPTZ,
  watch_seconds  INTEGER NOT NULL DEFAULT 0,
  ip             INET,
  user_agent     TEXT,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX livestream_viewer_stream_idx ON livestream_viewer_sessions (livestream_id);
CREATE INDEX livestream_viewer_user_idx   ON livestream_viewer_sessions (user_id) WHERE user_id IS NOT NULL;

-- ═══════════════════════════════════════════════════════════════════════
-- LIVESTREAM_COMMENTS — live chat during a stream
-- ═══════════════════════════════════════════════════════════════════════
CREATE TABLE livestream_comments (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  livestream_id  UUID NOT NULL REFERENCES livestreams(id) ON DELETE CASCADE,
  sender_id      UUID REFERENCES users(id) ON DELETE SET NULL,        -- NULL = anonymous
  body           TEXT NOT NULL CHECK (length(body) BETWEEN 1 AND 500),
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX livestream_comments_stream_idx ON livestream_comments (livestream_id, created_at);







-- ═══════════════════════════════════════════════════════════════════════
-- ENQUIRIES — buyer starts a conversation about a listing
-- ═══════════════════════════════════════════════════════════════════════
CREATE TABLE enquiries (
  id                                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  listing_id                         UUID NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
  buyer_id                           UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  farmer_id                          UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,  -- denormalized from listing for fast lookup
  quantity_requested                 NUMERIC(12,2) CHECK (quantity_requested > 0),
  proposed_price_per_unit_pesewas    BIGINT CHECK (proposed_price_per_unit_pesewas > 0),
  status                             enquiry_status NOT NULL DEFAULT 'open',
  last_activity_at                   TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_at                         TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at                         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX enquiries_buyer_idx        ON enquiries (buyer_id, last_activity_at DESC);
CREATE INDEX enquiries_farmer_idx       ON enquiries (farmer_id, last_activity_at DESC);
CREATE INDEX enquiries_listing_idx      ON enquiries (listing_id);
CREATE INDEX enquiries_open_idx         ON enquiries (farmer_id) WHERE status = 'open';

-- ═══════════════════════════════════════════════════════════════════════
-- ENQUIRY_MESSAGES — chat thread within an enquiry
-- ═══════════════════════════════════════════════════════════════════════
CREATE TABLE enquiry_messages (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  enquiry_id  UUID NOT NULL REFERENCES enquiries(id) ON DELETE CASCADE,
  sender_id   UUID NOT NULL REFERENCES users(id),
  body        TEXT NOT NULL CHECK (length(body) BETWEEN 1 AND 2000),
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX enquiry_messages_thread_idx ON enquiry_messages (enquiry_id, created_at);









-- ═══════════════════════════════════════════════════════════════════════
-- ORDERS — snapshot-based so later edits to listing/farm never rewrite history
-- ═══════════════════════════════════════════════════════════════════════
CREATE TABLE orders (
  id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  order_number           TEXT NOT NULL UNIQUE DEFAULT ('AM-' || nextval('order_number_seq')),
  listing_id             UUID NOT NULL REFERENCES listings(id) ON DELETE RESTRICT,
  enquiry_id             UUID REFERENCES enquiries(id) ON DELETE SET NULL,
  buyer_id               UUID NOT NULL REFERENCES users(id),
  farmer_id              UUID NOT NULL REFERENCES users(id),

  -- snapshots (do not read live listing later — this is the contract)
  crop_name              TEXT NOT NULL,
  listing_title          TEXT NOT NULL,
  unit                   quantity_unit NOT NULL,
  quantity               NUMERIC(12,2) NOT NULL CHECK (quantity > 0),
  unit_price_pesewas     BIGINT NOT NULL CHECK (unit_price_pesewas > 0),

  -- money (all in pesewas, integers — never floats for money)
  subtotal_pesewas       BIGINT NOT NULL CHECK (subtotal_pesewas >= 0),
  delivery_fee_pesewas   BIGINT NOT NULL DEFAULT 0 CHECK (delivery_fee_pesewas >= 0),
  platform_fee_pesewas   BIGINT NOT NULL DEFAULT 0 CHECK (platform_fee_pesewas >= 0),
  total_pesewas          BIGINT NOT NULL CHECK (total_pesewas >= 0),

  delivery_method        delivery_method NOT NULL,
  delivery_address       TEXT,
  delivery_lat           NUMERIC(9,6),
  delivery_lng           NUMERIC(9,6),
  requested_delivery_date DATE,
  buyer_note             TEXT,

  status                 order_status NOT NULL DEFAULT 'pending',
  accepted_at            TIMESTAMPTZ,
  completed_at           TIMESTAMPTZ,
  cancelled_reason       TEXT,
  created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT total_matches CHECK (
    total_pesewas = subtotal_pesewas + delivery_fee_pesewas + platform_fee_pesewas
  )
);

CREATE INDEX orders_buyer_idx    ON orders (buyer_id, created_at DESC);
CREATE INDEX orders_farmer_idx   ON orders (farmer_id, created_at DESC);
CREATE INDEX orders_status_idx   ON orders (status, created_at DESC);
CREATE INDEX orders_listing_idx  ON orders (listing_id);

-- ═══════════════════════════════════════════════════════════════════════
-- ORDER_STATUS_HISTORY — append-only audit of every transition
-- ═══════════════════════════════════════════════════════════════════════
CREATE TABLE order_status_history (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  order_id    UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  from_status order_status,
  to_status   order_status NOT NULL,
  actor_id    UUID REFERENCES users(id),                       -- NULL = system
  note        TEXT,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX order_status_history_order_idx ON order_status_history (order_id, created_at);

-- ═══════════════════════════════════════════════════════════════════════
-- PAYMENTS — incoming from buyer via Paystack
-- ═══════════════════════════════════════════════════════════════════════
CREATE TABLE payments (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  order_id          UUID NOT NULL REFERENCES orders(id) ON DELETE RESTRICT,
  provider          TEXT NOT NULL DEFAULT 'paystack',
  reference         TEXT NOT NULL UNIQUE,                      -- Paystack reference
  amount_pesewas    BIGINT NOT NULL CHECK (amount_pesewas > 0),
  currency          CHAR(3) NOT NULL DEFAULT 'GHS',
  channel           TEXT,                                      -- 'mobile_money' | 'card'
  status            payment_status NOT NULL DEFAULT 'initiated',
  provider_payload  JSONB,
  paid_at           TIMESTAMPTZ,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX payments_order_idx  ON payments (order_id);
CREATE INDEX payments_status_idx ON payments (status) WHERE status IN ('initiated','pending');

-- ═══════════════════════════════════════════════════════════════════════
-- PAYOUTS — outgoing to farmer's momo (via Paystack transfers)
-- ═══════════════════════════════════════════════════════════════════════
CREATE TABLE payouts (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  order_id           UUID NOT NULL REFERENCES orders(id) ON DELETE RESTRICT,
  farmer_id          UUID NOT NULL REFERENCES users(id),
  amount_pesewas     BIGINT NOT NULL CHECK (amount_pesewas > 0),
  status             payout_status NOT NULL DEFAULT 'pending',
  provider_reference TEXT UNIQUE,
  provider_payload   JSONB,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX payouts_farmer_idx ON payouts (farmer_id, created_at DESC);
CREATE INDEX payouts_status_idx ON payouts (status) WHERE status IN ('pending','processing');

-- ═══════════════════════════════════════════════════════════════════════
-- WEBHOOK_EVENTS — idempotency guard for Paystack + Cloudinary webhooks
-- ═══════════════════════════════════════════════════════════════════════
CREATE TABLE webhook_events (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  provider      TEXT NOT NULL,                                 -- 'paystack' | 'cloudinary'
  event_id      TEXT NOT NULL,                                 -- provider's unique event id
  payload       JSONB NOT NULL,
  processed_at  TIMESTAMPTZ,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (provider, event_id)                                  -- reject duplicates at DB level
);

CREATE INDEX webhook_events_unprocessed_idx ON webhook_events (provider) WHERE processed_at IS NULL;

-- ═══════════════════════════════════════════════════════════════════════
-- REVIEWS — one buyer review per completed order
-- ═══════════════════════════════════════════════════════════════════════
CREATE TABLE reviews (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  order_id     UUID NOT NULL UNIQUE REFERENCES orders(id) ON DELETE CASCADE,
  reviewer_id  UUID NOT NULL REFERENCES users(id),
  farmer_id    UUID NOT NULL REFERENCES users(id),
  rating       SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
  comment      TEXT CHECK (length(comment) <= 1000),
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX reviews_farmer_idx ON reviews (farmer_id, created_at DESC);








-- ═══════════════════════════════════════════════════════════════════════
-- NOTIFICATIONS — fan-out inbox (in-app + email mirror)
-- ═══════════════════════════════════════════════════════════════════════
CREATE TABLE notifications (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  channel    notification_channel NOT NULL DEFAULT 'in_app',
  type       TEXT NOT NULL,                                    -- 'enquiry.received', 'order.accepted', 'livestream.started'
  title      TEXT NOT NULL,
  body       TEXT,
  data       JSONB NOT NULL DEFAULT '{}',                      -- deep-link payload
  read_at    TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX notifications_user_unread_idx ON notifications (user_id, created_at DESC) WHERE read_at IS NULL;
CREATE INDEX notifications_user_idx        ON notifications (user_id, created_at DESC);

-- ═══════════════════════════════════════════════════════════════════════
-- AUDIT_LOGS — append-only record of privileged actions
-- ═══════════════════════════════════════════════════════════════════════
CREATE TABLE audit_logs (
  id           BIGSERIAL PRIMARY KEY,
  actor_id     UUID REFERENCES users(id),
  action       TEXT NOT NULL,                                  -- 'listing.removed_by_admin'
  entity_type  TEXT NOT NULL,
  entity_id    TEXT NOT NULL,
  meta         JSONB NOT NULL DEFAULT '{}',
  ip           INET,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX audit_logs_entity_idx ON audit_logs (entity_type, entity_id, created_at DESC);
CREATE INDEX audit_logs_actor_idx  ON audit_logs (actor_id, created_at DESC) WHERE actor_id IS NOT NULL;
