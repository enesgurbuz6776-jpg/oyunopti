
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
