import { createHmac } from "node:crypto";

export const FOOTBALL_WEBHOOK_URL =
  "https://futbolanaliz-backend.onrender.com/webapi/shopier/webhook";

/**
 * Called ONLY after OyunOpti has authenticated Shopier-Signature.
 * The destination independently fetches the paid order with Shopier PAT.
 * A dedicated HMAC secret prevents public callers from activating football access.
 */
export async function relayVerifiedFootballNotification(raw, secret, options = {}) {
  if (!secret || typeof secret !== "string" || secret.length < 32) {
    return { ok: false, status: "bridge_unconfigured" };
  }
  if (!Buffer.isBuffer(raw) || raw.length > 70 * 1024) {
    return { ok: false, status: "invalid_body" };
  }
  const stamp = String(Math.floor(Date.now() / 1000));
  const mac = createHmac("sha256", secret)
    .update(stamp + ".", "utf8").update(raw).digest("hex");
  const fetcher = options.fetcher || fetch;
  try {
    const response = await fetcher(FOOTBALL_WEBHOOK_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Shopier-Event": "order.created",
        "X-Football-Bridge-Timestamp": stamp,
        "X-Football-Bridge-Signature": mac,
      },
      body: raw,
      signal: AbortSignal.timeout(options.timeoutMs ?? 3500),
    });
    return { ok: response.ok, status: response.status };
  } catch {
    return { ok: false, status: "unreachable" };
  }
}
