CREATE TABLE IF NOT EXISTS pro_orders (
  id TEXT PRIMARY KEY,
  claim_sha256 CHAR(64) NOT NULL,
  device CHAR(32) NOT NULL,
  email TEXT NOT NULL,
  price_cents BIGINT NOT NULL CHECK (price_cents > 0),
  currency CHAR(3) NOT NULL,
  status TEXT NOT NULL CHECK (status IN (
    'creating','awaiting_payment','checkout_error','paid','review'
  )),
  product_id TEXT UNIQUE,
  payment_url TEXT,
  shopier_order_id TEXT UNIQUE,
  license_token TEXT,
  expires_on DATE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS pro_orders_device_expires_idx ON pro_orders(device, expires_on DESC);
CREATE INDEX IF NOT EXISTS pro_orders_created_idx ON pro_orders(created_at DESC);
