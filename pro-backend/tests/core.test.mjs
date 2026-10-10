import test from "node:test";
import assert from "node:assert/strict";
import { generateKeyPairSync, createHmac, verify } from "node:crypto";
import { createSignedLicense, extractOrderId, inspectShopierOrder, moneyCents,
  plusUtcDays, validDevice, verifiedPaidPurchase, verifyShopierHmac } from "../core.mjs";

const device = "A".repeat(32);
const productId = "479900123";
const paidOrder = { data: {
  id: "shp-12345", paymentStatus: "paid", totals: {total:"10.00"},
  currency:"USD",items:[{productId,quantity:1}] } };

test("Shopier raw-body signature accepts valid hex/base64 and rejects tampered body", () => {
  const raw=Buffer.from(JSON.stringify({id:"shp-12345"}));
  const key="fake-webhook-secret";
  const mac=createHmac("sha256",key).update(raw).digest();
  assert.equal(verifyShopierHmac(raw,mac.toString("hex"),key),true);
  assert.equal(verifyShopierHmac(raw,mac.toString("base64"),key),true);
  assert.equal(verifyShopierHmac(Buffer.from('{"id":"altered"}'),mac.toString("hex"),key),false);
  assert.equal(verifyShopierHmac(raw,"wrong",key),false);
});
test("device, money, and end dates", () => {
  assert.equal(validDevice(device),true);
  assert.equal(validDevice(device+"A"),false);
  assert.equal(moneyCents("10.00"),1000);
  assert.equal(moneyCents("10.001"),null);
  assert.equal(plusUtcDays("2026-10-10",30),"2026-11-09");
});
test("payment matching fails closed for wrong price, product, currency, quantity and payment status", () => {
  const normalized=inspectShopierOrder(paidOrder);
  assert.equal(extractOrderId(paidOrder),"shp-12345");
  assert.equal(verifiedPaidPurchase(normalized,{productId,cents:1000,currency:"USD"}),true);
  assert.equal(verifiedPaidPurchase(normalized,{productId,cents:990,currency:"USD"}),false);
  assert.equal(verifiedPaidPurchase(normalized,{productId:"111",cents:1000,currency:"USD"}),false);
  assert.equal(verifiedPaidPurchase(normalized,{productId,cents:1000,currency:"TRY"}),false);
  assert.equal(verifiedPaidPurchase(inspectShopierOrder({ ...paidOrder.data, paymentStatus:"unpaid" }),{productId,cents:1000,currency:"USD"}),false);
  assert.equal(verifiedPaidPurchase(inspectShopierOrder({ ...paidOrder.data, items:[{productId,quantity:2}] }),{productId,cents:1000,currency:"USD"}),false);
});
test("issue a signed Ed25519 license for the desktop's current schema", () => {
  const {privateKey,publicKey}=generateKeyPairSync("ed25519");
  const token=createSignedLicense(privateKey.export({format:"pem",type:"pkcs8"}),{
    device,expires:"2026-11-09",order:"shp-12345"});
  const segments=token.split(".");
  assert.equal(segments.length,2);
  assert.equal(verify(null,Buffer.from(segments[0],"base64url"),publicKey,Buffer.from(segments[1],"base64url")),true);
  const claims=JSON.parse(Buffer.from(segments[0],"base64url").toString("utf8"));
  assert.deepEqual({version:claims.version,plan:claims.plan,device:claims.device,expires:claims.expires},
    {version:1,plan:"pro",device,expires:"2026-11-09"});
});
