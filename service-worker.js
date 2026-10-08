const CACHE_NAME="oyunopti-pwa-v1";
const CORE=["./","./index.html","./offline.html","./style.css","./app.js","./config.js","./monetization.js","./site.webmanifest","./icon.svg","./aim-challenge.html","./valorant-cs2-sens.html","./edpi-hesaplama.html"];
self.addEventListener("install",event=>{event.waitUntil(caches.open(CACHE_NAME).then(cache=>cache.addAll(CORE)).then(()=>self.skipWaiting()))});
self.addEventListener("activate",event=>{event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE_NAME).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
self.addEventListener("fetch",event=>{const req=event.request;if(req.method!=="GET")return;const url=new URL(req.url);if(url.origin!==self.location.origin)return;
if(req.mode==="navigate"){event.respondWith(fetch(req).then(res=>{const copy=res.clone();caches.open(CACHE_NAME).then(cache=>cache.put(req,copy));return res}).catch(async()=>await caches.match(req,{ignoreSearch:true})||await caches.match("./offline.html")||await caches.match("./index.html")));return}
event.respondWith(fetch(req).then(res=>{if(res&&res.ok){const copy=res.clone();caches.open(CACHE_NAME).then(cache=>cache.put(req,copy))}return res}).catch(()=>caches.match(req,{ignoreSearch:true})))});
