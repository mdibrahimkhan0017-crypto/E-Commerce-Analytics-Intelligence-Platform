-- ===========================================================================
-- E-Commerce Analytics Platform — Database Schema
-- ===========================================================================
-- SQLite database schema with primary keys, foreign keys, NOT NULL
-- constraints, and performance indexes.
-- ===========================================================================

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- ── Customers ───────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS customers (
    customer_id   TEXT    PRIMARY KEY NOT NULL,
    email         TEXT    NOT NULL,
    registration_date TEXT NOT NULL,  -- ISO 8601 format: YYYY-MM-DD
    region        TEXT    NOT NULL,
    segment       TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_customers_region
    ON customers (region);

CREATE INDEX IF NOT EXISTS idx_customers_segment
    ON customers (segment);

-- ── Products ────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS products (
    product_id  TEXT    PRIMARY KEY NOT NULL,
    name        TEXT    NOT NULL,
    category    TEXT    NOT NULL,
    cost_price  REAL    NOT NULL CHECK (cost_price >= 0),
    list_price  REAL    NOT NULL CHECK (list_price > 0),
    is_active   INTEGER NOT NULL DEFAULT 1  -- 0 = inactive, 1 = active
);

CREATE INDEX IF NOT EXISTS idx_products_category
    ON products (category);

-- ── Orders ──────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS orders (
    order_id        TEXT PRIMARY KEY NOT NULL,
    customer_id     TEXT NOT NULL,
    order_date      TEXT NOT NULL,  -- ISO 8601 format: YYYY-MM-DD
    status          TEXT NOT NULL CHECK (status IN ('Completed','Refunded','Pending','Cancelled')),
    total_amount    REAL NOT NULL CHECK (total_amount >= 0),
    discount_amount REAL NOT NULL DEFAULT 0 CHECK (discount_amount >= 0),
    channel         TEXT NOT NULL CHECK (channel IN ('web','mobile','marketplace','in-store')),
    FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_orders_order_date
    ON orders (order_date);

CREATE INDEX IF NOT EXISTS idx_orders_customer_id
    ON orders (customer_id);

CREATE INDEX IF NOT EXISTS idx_orders_status
    ON orders (status);

CREATE INDEX IF NOT EXISTS idx_orders_channel
    ON orders (channel);

-- ── Order Items ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS order_items (
    item_id     TEXT    PRIMARY KEY NOT NULL,
    order_id    TEXT    NOT NULL,
    product_id  TEXT    NOT NULL,
    quantity    INTEGER NOT NULL CHECK (quantity >= 1),
    unit_price  REAL    NOT NULL CHECK (unit_price > 0),
    return_flag INTEGER NOT NULL DEFAULT 0,  -- 0 = not returned, 1 = returned
    FOREIGN KEY (order_id)   REFERENCES orders   (order_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products (product_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_order_items_order_id
    ON order_items (order_id);

CREATE INDEX IF NOT EXISTS idx_order_items_product_id
    ON order_items (product_id);

-- ── Views ───────────────────────────────────────────────────────────────────

CREATE VIEW IF NOT EXISTS v_order_summary AS
SELECT
    o.order_id,
    o.order_date,
    o.status,
    o.total_amount,
    o.discount_amount,
    o.channel,
    c.customer_id,
    c.email          AS customer_email,
    c.region         AS customer_region,
    c.segment        AS customer_segment,
    oi.item_id,
    oi.quantity,
    oi.unit_price,
    oi.return_flag,
    p.product_id,
    p.name           AS product_name,
    p.category       AS product_category,
    p.cost_price,
    p.list_price,
    (oi.quantity * oi.unit_price) AS line_total,
    (oi.quantity * (oi.unit_price - p.cost_price)) AS line_margin
FROM orders o
JOIN order_items oi ON o.order_id   = oi.order_id
JOIN customers  c  ON o.customer_id = c.customer_id
JOIN products   p  ON oi.product_id = p.product_id;
