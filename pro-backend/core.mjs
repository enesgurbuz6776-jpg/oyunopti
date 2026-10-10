import { createHmac, createPrivateKey, createPublicKey, randomBytes, sign, timingSafeEqual } from "node:crypto";

/** Shopier signs the *raw* body with HMAC-SHA256 (hex or base64). */
export function verifyShopierHmac(raw, signature, secret) {
  if (!secret || !signature || !Buffer.isBuffer(raw)) return false;
  const expected = createHmac("sha256", secret).update(raw).digest();
  let received;
  const input = String(signature).trim();
  if (/^[a-f0-9]{64}$/i.test(input)) received = Buffer.from(input, "hex");
  else if (/^[A-Za-z0-9+/]{43}=$|^[A-Za-z0-9+/]{44}$/.test(input)) received = Buffer.from(input, "base64");
  else return false;
  return received.length === expected.length && timingSafeEqual(received, expected);
}

export function validDevice(device) {
  return /^[0-9A-F]{32}$/.test(String(device || "").trim().toUpperCase());
}
export function moneyCents(value) {
  const str = String(value ?? "").trim();
  if (!/^\d{1,9}(?:\.\d{1,2})?$/.test(str)) return null;
  const [whole, fraction = ""] = str.split(".");
  const result = BigInt(whole) * 100n + BigInt(fraction.padEnd(2, "0"));
  return result > BigInt(Number.MAX_SAFE_INTEGER) ? null : Number(result);
}
export function utcDay(date = new Date()) {
  return date.toISOString().slice(0, 10);
}
export function plusUtcDays(isoDay, days = 30) {
  const date = new Date(isoDay + "T00:00:00.000Z");
  if (Number.isNaN(date.getTime())) throw new Error("Invalid UTC date");
  date.setUTCDate(date.getUTCDate() + days);
  return utcDay(date);
}
export function createSignedLicense(pem, { device, expires, order }) {
  if (!validDevice(device) || !/^\d{4}-\d{2}-\d{2}$/.test(expires) || !/^[a-zA-Z0-9:_-]{5,120}$/.test(String(order)))
    throw new Error("Invalid license claims");
  const data = { version: 1, plan: "pro", device: device.toUpperCase(),
    expires, order: String(order), nonce: randomBytes(8).toString("hex") };
  const payload = Buffer.from(JSON.stringify(data));
  const signature = sign(null, payload, createPrivateKey(pem));
  return payload.toString("base64url") + "." + signature.toString("base64url");
}

/** Validate signed licenses against the public Ed25519 key embedded in Windows. */
export function licenseMatchesApp(token, expectedPublicKeyBase64) {
  const parts = String(token).split(".");
  if (parts.length !== 2) return false;
  const data = Buffer.from(parts[0], "base64url");
  const sig = Buffer.from(parts[1], "base64url");
  const publicKey = createPublicKey({ key: Buffer.concat([
    Buffer.from("302a300506032b6570032100", "hex"),
    Buffer.from(expectedPublicKeyBase64, "base64")]),
    format: "der", type: "spki" });
  const { verify } = requireVerify();
  return sig.length === 64 && verify(null, data, publicKey, sig);
}
function requireVerify() { return { verify: builtinVerify }; }
import { verify as builtinVerify } from "node:crypto";

function unwrapOrder(value) {
  if (!value || typeof value !== "object") return null;
  return value.data?.order || value.order || value.data || value;
}
export function extractOrderId(body) {
  const event = unwrapOrder(body);
  const id = event?.id ?? event?.orderId ?? event?.order_id;
  if (!/^[a-zA-Z0-9_-]{1,90}$/.test(String(id ?? ""))) return null;
  return String(id);
}
export function inspectShopierOrder(response) {
  const o = unwrapOrder(response);
  if (!o || typeof o !== "object") return null;
  const paymentStatus = String(o.paymentStatus ?? o.payment_status ?? o.payment?.status ?? "").trim().toLowerCase();
  const amount = o.totals?.total ?? o.total ?? o.totalAmount ?? o.total_amount ?? o.amount;
  const currency = String(o.currency ?? o.totals?.currency ?? o.priceData?.currency ?? "").toUpperCase();
  const lines = o.items ?? o.lineItems ?? o.line_items ?? o.orderItems ?? o.order_items ?? o.products;
  if (!Array.isArray(lines)) return null;
  const items = lines.map(item => ({
    productId: String(item?.productId ?? item?.product_id ?? item?.product?.id ?? ""),
    quantity: Number(item.quantity ?? item.qty ?? 1),
  }));
  return { orderId: extractOrderId(o), paymentStatus, amountCents: moneyCents(amount), currency, items,
    buyerEmail: o.buyer?.email ?? o.customer?.email ?? o.buyerEmail ?? null };
}
/** No license unless a paid Shopier API response exactly matches our unique one-item checkout. */
export function verifiedPaidPurchase(order, { productId, cents, currency }) {
  return !!(order && order.orderId && order.paymentStatus === "paid" &&
    order.currency === currency && order.amountCents === cents &&
    order.items.length === 1 && order.items[0].productId === String(productId) &&
    order.items[0].quantity === 1);
}
