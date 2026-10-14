import test from "node:test";
import assert from "node:assert/strict";
import { createHmac } from "node:crypto";
import { relayVerifiedFootballNotification, FOOTBALL_WEBHOOK_URL } from "../football-bridge.mjs";

test("bridge signs exact raw notification and timestamp", async () => {
  const payload = Buffer.from('{"id":"ORDER-77"}');
  const secret = "unit-test-shared-secret-which-is-long-enough";
  let seen = null;
  const outcome = await relayVerifiedFootballNotification(payload, secret, {
    fetcher: async (url, request) => {
      seen = { url, request };
      return { ok: true, status: 200 };
    },
  });
  assert.deepEqual(outcome, { ok: true, status: 200 });
  assert.equal(seen.url, FOOTBALL_WEBHOOK_URL);
  assert.deepEqual(seen.request.body, payload);
  const stamp = seen.request.headers["X-Football-Bridge-Timestamp"];
  const sig = createHmac("sha256", secret).update(stamp + ".").update(payload).digest("hex");
  assert.equal(seen.request.headers["X-Football-Bridge-Signature"], sig);
  assert.equal(seen.request.headers["Shopier-Event"], "order.created");
});

test("bridge blocks calls when secret is not configured", async () => {
  let called = false;
  const r = await relayVerifiedFootballNotification(Buffer.from("{}"), "", {
    fetcher: async () => { called = true; }
  });
  assert.equal(r.ok, false);
  assert.equal(called, false);
});

test("bridge rejects oversized notification bodies", async () => {
  const r = await relayVerifiedFootballNotification(Buffer.alloc(71000), "x".repeat(40));
  assert.deepEqual(r, { ok: false, status: "invalid_body" });
});

test("bridge gracefully reports destination errors", async () => {
  const r = await relayVerifiedFootballNotification(Buffer.from("{}"), "x".repeat(40), {
    fetcher: async () => { throw new Error("Connection refused"); },
  });
  assert.deepEqual(r, { ok: false, status: "unreachable" });
});
