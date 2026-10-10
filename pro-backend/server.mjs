import express from "express";
import pg from "pg";
import { ShopierApiClient, ShopierPaymentFlow } from "@nopeion/shopier";
import { createHash, randomBytes } from "node:crypto";
import { createSignedLicense, extractOrderId, inspectShopierOrder, moneyCents,
  plusUtcDays, utcDay, validDevice, verifiedPaidPurchase, verifyShopierHmac } from "./core.mjs";

const PORT = Number(process.env.PORT || 3000);
const ORIGIN = process.env.SITE_ORIGIN || "https://oyunopti.com";
const PRICE = process.env.PRO_PRICE || "10.00";
const CURRENCY = (process.env.PRO_CURRENCY || "USD").toUpperCase();
const PRICE_CENTS = moneyCents(PRICE);
const READY = !!(process.env.SALE_ENABLED === "true" && process.env.DATABASE_URL &&
  process.env.SHOPIER_PAT && process.env.SHOPIER_WEBHOOK_TOKEN &&
  process.env.SHOPIER_SHOP_SLUG && process.env.LICENSE_PRIVATE_KEY_PEM &&
  PRICE_CENTS > 0 && ["USD", "TRY", "EUR"].includes(CURRENCY));

const pool = process.env.DATABASE_URL ? new pg.Pool({
  connectionString: process.env.DATABASE_URL, max: 6,
  ssl: process.env.DATABASE_SSL === "true" ? { rejectUnauthorized: true } : undefined,
}) : null;
const shopier = process.env.SHOPIER_PAT
  ? new ShopierApiClient({ pat: process.env.SHOPIER_PAT }) : null;
const payments = shopier ? new ShopierPaymentFlow({ client: shopier }) : null;
const app = express();
app.disable("x-powered-by");
app.use((req, res, next) => {
  res.setHeader("Vary", "Origin");
  if (req.headers.origin === ORIGIN) {
    res.setHeader("Access-Control-Allow-Origin", ORIGIN);
    res.setHeader("Access-Control-Allow-Methods", "GET,POST,OPTIONS");
    res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  }
  if (req.method === "OPTIONS") return res.status(204).end();
  next();
});
const ipHits = new Map();
function throttle(req, res, next) {
  const ip = req.ip || "unknown";
  const now = Date.now();
  const recent = (ipHits.get(ip) || []).filter(t => now - t < 60 * 60 * 1000);
  if (recent.length >= 10) return res.status(429).json({ error: "Çok fazla deneme. Sonra tekrar deneyin." });
  recent.push(now);
  ipHits.set(ip, recent);
  if (ipHits.size > 5000) ipHits.clear();
  next();
}
function required(req, res, next) {
  if (!READY) return res.status(503).json({ error: "Ödeme bağlantısı henüz açılmadı." });
  next();
}
function safeResponse(res, status, msg) { return res.status(status).json({ error: msg }); }
const sha = value => createHash("sha256").update(value).digest("hex");
const rand = size => randomBytes(size).toString("base64url");

app.get("/api/health", (req, res) => {
  res.setHeader("Cache-Control", "no-store");
  res.json({ service: "OyunOpti Pro", paymentsEnabled: READY, currency: CURRENCY,
    price: PRICE, termDays: 30, recurringCharge: false });
});

/**
 * Customer gives the device code from the EXE and their email.
 * We create a unique temporary Shopier product for this payment so the webhook
 * can reconcile a specific paid item with exactly one device / checkout session.
 */
app.post("/api/checkout", express.json({ limit: "12kb" }), throttle, required, async (req, res) => {
  const device = String(req.body?.device || "").trim().toUpperCase();
  const email = String(req.body?.email || "").trim().toLowerCase();
  if (!validDevice(device)) return safeResponse(res, 400, "Geçerli 32 karakterli cihaz kodu girin.");
  if (email.length > 240 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))
    return safeResponse(res, 400, "Geçerli bir e-posta adresi girin.");
  const session = "OO-" + randomBytes(18).toString("hex");
  const secret = rand(32);
  const client = await pool.connect();
  try {
    await client.query("INSERT INTO pro_orders(id,claim_sha256,device,email,price_cents,currency,status) VALUES ($1,$2,$3,$4,$5,$6,'creating')",
      [session, sha(secret), device, email, PRICE_CENTS, CURRENCY]);
  } finally { client.release(); }
  try {
    const pay = await payments.createPaymentLink({
      title: "OyunOpti Pro 30 Gun " + session.slice(-12),
      amount: PRICE, currency: CURRENCY, imageUrl: "https://oyunopti.com/icon.svg",
      orderId: session, hostedCheckout: true, shopSlug: process.env.SHOPIER_SHOP_SLUG,
    });
    const productId = String(pay.productId ?? "");
    const url = String(pay.paymentUrl ?? "");
    if (!/^\d{1,32}$/.test(productId) || !/^https:\/\/(?:www\.)?shopier\.com\//i.test(url))
      throw new Error("Shopier ürün kaydı/ödeme bağlantısı eksik");
    await pool.query("UPDATE pro_orders SET product_id=$1,payment_url=$2,status='awaiting_payment' WHERE id=$3",
      [productId, url, session]);
    res.setHeader("Cache-Control", "no-store");
    res.json({ session, secret, paymentUrl: url, termDays: 30 });
  } catch (error) {
    await pool.query("UPDATE pro_orders SET status='checkout_error' WHERE id=$1", [session]).catch(() => {});
    console.error("Checkout creation failed:", error?.message || "unknown");
    safeResponse(res, 502, "Shopier ödeme bağlantısı oluşturulamadı. Ücret çekildiyse yeni ödeme yapmadan destekle görüşün.");
  }
});

app.post("/api/claim", express.json({ limit: "12kb" }), throttle, required, async (req, res) => {
  const session = String(req.body?.session || "");
  const secret = String(req.body?.secret || "");
  if (!/^OO-[a-f0-9]{36}$/.test(session) || !/^[\w-]{35,100}$/.test(secret))
    return safeResponse(res, 400, "Geçersiz ödeme takip bilgisi.");
  const data = await pool.query("SELECT claim_sha256,status,license_token,expires_on FROM pro_orders WHERE id=$1", [session]);
  const row = data.rows[0];
  if (!row || sha(secret) !== row.claim_sha256)
    return safeResponse(res, 404, "İşlem bulunamadı.");
  res.setHeader("Cache-Control", "no-store");
  if (row.status === "paid" && row.license_token)
    return res.json({ status: "paid", license: row.license_token, expires: row.expires_on });
  return res.json({ status: row.status });
});

/** Query the authoritative Shopier PAT order API. Never issue a key on redirect or unsigned payload. */
async function retrieveOrder(id) {
  const ac = new AbortController();
  const t = setTimeout(() => ac.abort(), 8000);
  try {
    const response = await fetch("https://api.shopier.com/v1/orders/" + encodeURIComponent(id), {
      headers: { Authorization: "Bearer " + process.env.SHOPIER_PAT, Accept: "application/json" },
      signal: ac.signal,
    });
    if (!response.ok) throw new Error("Shopier PAT order lookup failed: " + response.status);
    return response.json();
  } finally { clearTimeout(t); }
}

app.post("/api/shopier/webhook", express.raw({ type: "*/*", limit: "70kb" }), required, async (req, res) => {
  const raw = req.body;
  const signature = req.get("shopier-signature");
  if (!verifyShopierHmac(raw, signature, process.env.SHOPIER_WEBHOOK_TOKEN))
    return safeResponse(res, 401, "Geçersiz Shopier imzası.");
  const event = String(req.get("shopier-event") || "").toLowerCase();
  if (event !== "order.created") return res.status(200).send("ignored");
  let body;
  try { body = JSON.parse(raw.toString("utf8")); }
  catch { return safeResponse(res, 400, "Bozuk Shopier verisi."); }
  const shopierId = extractOrderId(body);
  if (!shopierId) return safeResponse(res, 400, "Shopier sipariş kimliği eksik.");
  try {
    const order = inspectShopierOrder(await retrieveOrder(shopierId));
    if (!order || order.orderId !== shopierId || order.items.length !== 1 ||
        !/^\d{1,32}$/.test(order.items[0].productId)) {
      console.error("Unrecognized Shopier order schema:", shopierId);
      return safeResponse(res, 422, "Sipariş ürünü doğrulanamadı.");
    }
    const db = await pool.connect();
    try {
      await db.query("BEGIN");
      const match = await db.query(
        "SELECT * FROM pro_orders WHERE product_id=$1 FOR UPDATE", [order.items[0].productId]);
      const row = match.rows[0];
      if (!row) { await db.query("ROLLBACK"); return res.status(200).send("unknown product ignored"); }
      if (row.status === "paid") { await db.query("COMMIT"); return res.status(200).send("already handled"); }
      if (row.status !== "awaiting_payment" || !verifiedPaidPurchase(order, {
        productId: row.product_id, cents: Number(row.price_cents), currency: row.currency,
      })) {
        await db.query("UPDATE pro_orders SET status='review', updated_at=NOW() WHERE id=$1", [row.id]);
        await db.query("COMMIT");
        return safeResponse(res, 422, "Tutar, ödeme durumu veya ürün eşleşmiyor.");
      }
      const existing = await db.query(
        "SELECT MAX(expires_on)::text AS end_day FROM pro_orders WHERE device=$1 AND status='paid'", [row.device]);
      const base = existing.rows[0]?.end_day > utcDay() ? existing.rows[0].end_day : utcDay();
      const expiry = plusUtcDays(base, 30);
      const key = createSignedLicense(process.env.LICENSE_PRIVATE_KEY_PEM.replace(/\\n/g,"\n"), {
        device: row.device, expires: expiry, order: shopierId,
      });
      await db.query(
        "UPDATE pro_orders SET status='paid', shopier_order_id=$1,license_token=$2,expires_on=$3,updated_at=NOW() WHERE id=$4",
        [shopierId, key, expiry, row.id]);
      await db.query("COMMIT");
      console.log("License automatically issued for verified order", shopierId);
      return res.status(200).send("success");
    } catch (error) {
      await db.query("ROLLBACK").catch(() => {});
      throw error;
    } finally { db.release(); }
  } catch (error) {
    console.error("Shopier callback handling failed", error?.message || "unknown");
    return safeResponse(res, 503, "Sipariş tekrar kontrol edilecek.");
  }
});

app.use((err, req, res, next) => {
  console.error("HTTP error", err?.message || "unknown");
  safeResponse(res, 400, "İstek işlenemedi.");
});
app.listen(PORT, () => console.log("OyunOpti Pro payment automation on port", PORT, "| payments enabled:", READY));
