import test from "node:test";
import assert from "node:assert/strict";
import { createServer } from "node:net";
import { spawn } from "node:child_process";
import { createHmac } from "node:crypto";

function freePort() {
  return new Promise((resolve,reject) => {
    const srv=createServer();
    srv.on("error",reject);
    srv.listen(0,"127.0.0.1",()=> {
      const port=srv.address().port;
      srv.close(err=>err?reject(err):resolve(port));
    });
  });
}
test("Shopier webhook: valid HMAC accepted in diagnostics mode, forged rejected, license issuing disabled", async t => {
  const port=await freePort();
  const secret="test-webhook-secret-no-production-key";
  const child=spawn(process.execPath,["server.mjs"],{
    cwd:new URL("..",import.meta.url).pathname,
    env:{...process.env,PORT:String(port),DATABASE_URL:"",SHOPIER_PAT:"",
      SHOPIER_WEBHOOK_TOKEN:secret,LICENSE_PRIVATE_KEY_PEM:"",SALE_ENABLED:"false"},
    stdio:["ignore","pipe","pipe"],
  });
  t.after(()=>{if(!child.killed)child.kill()});
  let alive=false;
  for(let i=0;i<60;i++){
    if(child.exitCode!==null)throw new Error("Server exited before health check");
    try{
      const r=await fetch("http://127.0.0.1:"+port+"/api/health");
      if(r.ok){
        const j=await r.json();
        assert.equal(j.paymentsEnabled,false);
        alive=true;break;
      }
    }catch{}
    await new Promise(resolve=>setTimeout(resolve,100));
  }
  assert.ok(alive,"Backend failed to start");
  const raw=JSON.stringify({id:"test-order-id",status:"paid"});
  const sig=createHmac("sha256",secret).update(raw).digest("hex");
  const endpoint="http://127.0.0.1:"+port+"/api/shopier/webhook";
  const headers={"content-type":"application/json","shopier-event":"order.created",
    "shopier-signature":sig};
  const good=await fetch(endpoint,{method:"POST",headers,body:raw});
  assert.equal(good.status,200);
  assert.match(await good.text(),/sales disabled/);
  const bad=await fetch(endpoint,{method:"POST",
    headers:{...headers,"shopier-signature":"0".repeat(64)},body:raw});
  assert.equal(bad.status,401);
  const checkout=await fetch("http://127.0.0.1:"+port+"/api/checkout",{
    method:"POST",headers:{"content-type":"application/json"},
    body:JSON.stringify({device:"A".repeat(32),email:"test@example.com"})});
  assert.equal(checkout.status,503);
});
