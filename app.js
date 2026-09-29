
const yaw={valorant:.07,cs2:.022,apex:.022};
const names={valorant:"Valorant",cs2:"CS2",apex:"Apex Legends"};
const $=s=>document.querySelector(s);
const fmt=(n,d=3)=>Number(n).toLocaleString("tr-TR",{maximumFractionDigits:d});
function show(el,html){if(!el)return;el.innerHTML=html;el.classList.add("show")}
function humanTime(sec){sec=Math.round(sec);const h=Math.floor(sec/3600),m=Math.floor((sec%3600)/60),s=sec%60;return [h?`${h} sa`:"",m?`${m} dk`:"",(!h&&s)?`${s} sn`:""].filter(Boolean).join(" ")}

if($("#calcSens"))$("#calcSens").addEventListener("click",()=>{
 const from=$("#sensFrom").value,to=$("#sensTo").value,s=parseFloat($("#sensValue").value),dpi=parseFloat($("#sensDpi").value||0);
 if(!(s>0))return show($("#sensResult"),"Geçerli bir sensitivity değeri gir.");
 const target=s*yaw[from]/yaw[to]; const counts360=360/(s*yaw[from]); const cm=dpi>0?counts360/dpi*2.54:null;
 show($("#sensResult"),`<div class="result-grid"><div class="result-item"><small>${names[from]}</small><b>${fmt(s,4)}</b></div><div class="result-item"><small>${names[to]}</small><b>${fmt(target,4)}</b></div><div class="result-item"><small>${dpi>0?"Yaklaşık cm/360":"Dönüşüm"}</small><b>${dpi>0?fmt(cm,2)+" cm":"Hazır"}</b></div></div><div class="sub">Aynı yaklaşık fiziksel 360° dönüş mesafesini hedefler. FOV ve oyun motoru farkları hissiyatı etkileyebilir.</div>`);
});

if($("#calcEdpi"))$("#calcEdpi").addEventListener("click",()=>{
 const game=$("#edpiGame").value,dpi=parseFloat($("#edpiDpi").value),sens=parseFloat($("#edpiSens").value);
 if(!(dpi>0&&sens>0))return show($("#edpiResult"),"Geçerli DPI ve sensitivity gir.");
 const edpi=dpi*sens,cm=360/(sens*yaw[game])/dpi*2.54;
 show($("#edpiResult"),`<div class="result-grid"><div class="result-item"><small>eDPI</small><b>${fmt(edpi,1)}</b></div><div class="result-item"><small>cm/360</small><b>${fmt(cm,2)} cm</b></div><div class="result-item"><small>Oyun</small><b>${names[game]}</b></div></div>`);
});

if($("#calcPpi"))$("#calcPpi").addEventListener("click",()=>{
 const size=parseFloat($("#ppiSize").value),w=parseFloat($("#ppiW").value),h=parseFloat($("#ppiH").value);
 if(!(size>0&&w>0&&h>0))return show($("#ppiResult"),"Geçerli değerler gir.");
 const ppi=Math.sqrt(w*w+h*h)/size,pitch=25.4/ppi;
 show($("#ppiResult"),`<div class="result-grid"><div class="result-item"><small>PPI</small><b>${fmt(ppi,1)}</b></div><div class="result-item"><small>Piksel aralığı</small><b>${fmt(pitch,3)} mm</b></div><div class="result-item"><small>Çözünürlük</small><b>${w}×${h}</b></div></div>`);
});

if($("#calcDownload"))$("#calcDownload").addEventListener("click",()=>{
 const gb=parseFloat($("#dlSize").value),mbps=parseFloat($("#dlMbps").value),eff=parseFloat($("#dlEfficiency").value);
 if(!(gb>0&&mbps>0))return show($("#dlResult"),"Geçerli değerler gir.");
 const seconds=(gb*8*1000)/(mbps*eff),real=mbps*eff;
 show($("#dlResult"),`<div class="result-grid"><div class="result-item"><small>Tahmini süre</small><b>${humanTime(seconds)}</b></div><div class="result-item"><small>Efektif hız</small><b>${fmt(real,1)} Mbps</b></div><div class="result-item"><small>Yaklaşık aktarım</small><b>${fmt(real/8,1)} MB/s</b></div></div><div class="sub">Sunucu, Wi‑Fi ve disk hızı gerçek süreyi değiştirebilir.</div>`);
});

if($("#calcHz"))$("#calcHz").addEventListener("click",()=>{
 const hz=parseFloat($("#hzValue").value); if(!(hz>0))return show($("#hzResult"),"Geçerli Hz gir.");
 const ms=1000/hz;
 show($("#hzResult"),`<div class="result-grid"><div class="result-item"><small>Yenileme</small><b>${fmt(hz,0)} Hz</b></div><div class="result-item"><small>Kare süresi</small><b>${fmt(ms,2)} ms</b></div><div class="result-item"><small>60 Hz'e göre</small><b>${hz>60?fmt((1000/60)-ms,2)+" ms kısa":"—"}</b></div></div>`);
});
document.querySelectorAll("[data-year]").forEach(x=>x.textContent=new Date().getFullYear());

// ===== V3 TRAFIK =====
function v3num(sel){const e=document.querySelector(sel);return e?parseFloat(String(e.value).replace(",",".")):NaN}
function v3show(sel,html){const e=document.querySelector(sel);if(!e)return;e.innerHTML=html;e.classList.add("show")}
function v3fmt(n,d=2){return Number(n).toLocaleString("tr-TR",{maximumFractionDigits:d})}

const btnVal=document.querySelector("#calcValorantEdpi");
if(btnVal) btnVal.addEventListener("click",()=>{
  const dpi=v3num("#valDpi"), sens=v3num("#valSens");
  if(!(dpi>0&&sens>0)) return v3show("#valEdpiResult","Geçerli DPI ve sensitivity gir.");
  const edpi=dpi*sens, cm=360/(sens*0.07)/dpi*2.54;
  v3show("#valEdpiResult",`<div class="metric-row">
  <div class="metric"><small>eDPI</small><b>${v3fmt(edpi,1)}</b></div>
  <div class="metric"><small>cm/360</small><b>${v3fmt(cm,2)} cm</b></div>
  <div class="metric"><small>DPI</small><b>${v3fmt(dpi,0)}</b></div>
  <div class="metric"><small>Sens</small><b>${v3fmt(sens,4)}</b></div></div>`);
});

const btnCs=document.querySelector("#calcCs2Edpi");
if(btnCs) btnCs.addEventListener("click",()=>{
  const dpi=v3num("#csDpi"), sens=v3num("#csSens");
  if(!(dpi>0&&sens>0)) return v3show("#csEdpiResult","Geçerli DPI ve sensitivity gir.");
  const edpi=dpi*sens, cm=360/(sens*0.022)/dpi*2.54;
  v3show("#csEdpiResult",`<div class="metric-row">
  <div class="metric"><small>eDPI</small><b>${v3fmt(edpi,1)}</b></div>
  <div class="metric"><small>cm/360</small><b>${v3fmt(cm,2)} cm</b></div>
  <div class="metric"><small>DPI</small><b>${v3fmt(dpi,0)}</b></div>
  <div class="metric"><small>Sens</small><b>${v3fmt(sens,4)}</b></div></div>`);
});

const btnDpi=document.querySelector("#calcDpiSens");
if(btnDpi) btnDpi.addEventListener("click",()=>{
  const oldDpi=v3num("#oldDpi"), oldSens=v3num("#oldSens"), newDpi=v3num("#newDpi");
  if(!(oldDpi>0&&oldSens>0&&newDpi>0)) return v3show("#dpiSensResult","Geçerli değerler gir.");
  const newSens=oldDpi*oldSens/newDpi;
  v3show("#dpiSensResult",`<div class="metric-row">
  <div class="metric"><small>Eski DPI</small><b>${v3fmt(oldDpi,0)}</b></div>
  <div class="metric"><small>Eski sens</small><b>${v3fmt(oldSens,4)}</b></div>
  <div class="metric"><small>Yeni DPI</small><b>${v3fmt(newDpi,0)}</b></div>
  <div class="metric"><small>Yeni sens</small><b>${v3fmt(newSens,4)}</b></div></div>
  <div class="sub">Aynı eDPI değerini korur.</div>`);
});

const btnFps=document.querySelector("#calcFpsMs");
if(btnFps) btnFps.addEventListener("click",()=>{
  const fps=v3num("#fpsValue");
  if(!(fps>0)) return v3show("#fpsResult","Geçerli FPS değeri gir.");
  const ms=1000/fps;
  v3show("#fpsResult",`<div class="metric-row">
  <div class="metric"><small>FPS</small><b>${v3fmt(fps,0)}</b></div>
  <div class="metric"><small>Frame time</small><b>${v3fmt(ms,2)} ms</b></div>
  <div class="metric"><small>60 FPS'e fark</small><b>${fps>60?v3fmt((1000/60)-ms,2)+" ms":"—"}</b></div>
  <div class="metric"><small>240 FPS'e fark</small><b>${v3fmt(Math.abs((1000/240)-ms),2)} ms</b></div></div>`);
});
document.querySelectorAll("[data-fps]").forEach(b=>b.addEventListener("click",()=>{document.querySelector("#fpsValue").value=b.dataset.fps;btnFps.click()}));

const btnPoll=document.querySelector("#calcPolling");
if(btnPoll) btnPoll.addEventListener("click",()=>{
  const hz=v3num("#pollHz");
  if(!(hz>0)) return v3show("#pollResult","Geçerli polling rate gir.");
  const interval=1000/hz, avg=interval/2;
  v3show("#pollResult",`<div class="metric-row">
  <div class="metric"><small>Polling rate</small><b>${v3fmt(hz,0)} Hz</b></div>
  <div class="metric"><small>Rapor aralığı</small><b>${v3fmt(interval,3)} ms</b></div>
  <div class="metric"><small>Ort. bekleme</small><b>~${v3fmt(avg,3)} ms</b></div>
  <div class="metric"><small>1000 Hz'e göre</small><b>${hz>=1000?"≤ 1 ms":v3fmt(interval-1,3)+" ms fazla"}</b></div></div>
  <div class="sub">Bu teorik USB raporlama aralığıdır; gerçek sistem gecikmesi değildir.</div>`);
});
document.querySelectorAll("[data-poll]").forEach(b=>b.addEventListener("click",()=>{document.querySelector("#pollHz").value=b.dataset.poll;btnPoll.click()}));

const btnAspect=document.querySelector("#calcAspect");
if(btnAspect) btnAspect.addEventListener("click",()=>{
  const w=v3num("#resW"), h=v3num("#resH");
  if(!(w>0&&h>0)) return v3show("#aspectResult","Geçerli çözünürlük gir.");
  const g=(a,b)=>b?g(b,a%b):a, d=g(Math.round(w),Math.round(h));
  const ratioW=Math.round(w)/d, ratioH=Math.round(h)/d;
  const decimal=w/h;
  v3show("#aspectResult",`<div class="metric-row">
  <div class="metric"><small>Çözünürlük</small><b>${Math.round(w)}×${Math.round(h)}</b></div>
  <div class="metric"><small>En-boy oranı</small><b>${ratioW}:${ratioH}</b></div>
  <div class="metric"><small>Ondalık oran</small><b>${v3fmt(decimal,3)}</b></div>
  <div class="metric"><small>Toplam piksel</small><b>${v3fmt((w*h)/1e6,2)} MP</b></div></div>`);
});
