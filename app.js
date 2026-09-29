
const yaw = { valorant: 0.07, cs2: 0.022, apex: 0.022 };
const names = { valorant: "Valorant", cs2: "CS2", apex: "Apex Legends" };
const $ = s => document.querySelector(s);
const fmt = (n, d=3) => Number(n).toLocaleString("tr-TR",{maximumFractionDigits:d});

function show(el, html){ el.innerHTML = html; el.classList.add("show"); }

document.querySelectorAll("[data-jump]").forEach(b=>{
  b.addEventListener("click",()=>document.getElementById(b.dataset.jump).scrollIntoView({behavior:"smooth",block:"start"}));
});

$("#calcSens").addEventListener("click",()=>{
  const from=$("#sensFrom").value, to=$("#sensTo").value;
  const s=parseFloat($("#sensValue").value), dpi=parseFloat($("#sensDpi").value||0);
  if(!(s>0)){return show($("#sensResult"),"Geçerli bir sensitivity değeri gir.");}
  const target=s*yaw[from]/yaw[to];
  let extra="";
  if(dpi>0){
    const counts360=360/(s*yaw[from]);
    const cm360=counts360/dpi*2.54;
    extra=`<div class="result-grid">
      <div class="result-item"><small>${names[from]}</small><b>${fmt(s,4)}</b></div>
      <div class="result-item"><small>${names[to]}</small><b>${fmt(target,4)}</b></div>
      <div class="result-item"><small>Yaklaşık cm/360</small><b>${fmt(cm360,2)} cm</b></div>
    </div>`;
  } else {
    extra=`<div class="main-result">${fmt(target,4)}</div>`;
  }
  show($("#sensResult"),`${extra}<div class="sub">Yaklaşık aynı fiziksel 360° dönüş mesafesini hedefler. Oyun motoru/FOV farkı hissiyatı değiştirebilir.</div>`);
});

$("#calcEdpi").addEventListener("click",()=>{
  const game=$("#edpiGame").value, dpi=parseFloat($("#edpiDpi").value), sens=parseFloat($("#edpiSens").value);
  if(!(dpi>0&&sens>0)){return show($("#edpiResult"),"Geçerli DPI ve sensitivity gir.");}
  const edpi=dpi*sens;
  const cm=360/(sens*yaw[game])/dpi*2.54;
  show($("#edpiResult"),`<div class="result-grid">
    <div class="result-item"><small>eDPI</small><b>${fmt(edpi,1)}</b></div>
    <div class="result-item"><small>cm/360</small><b>${fmt(cm,2)} cm</b></div>
    <div class="result-item"><small>Oyun</small><b>${names[game]}</b></div>
  </div><div class="sub">eDPI en sağlıklı şekilde aynı oyun içindeki ayarları karşılaştırmak için kullanılır.</div>`);
});

$("#calcPpi").addEventListener("click",()=>{
  const size=parseFloat($("#ppiSize").value), w=parseFloat($("#ppiW").value), h=parseFloat($("#ppiH").value);
  if(!(size>0&&w>0&&h>0)){return show($("#ppiResult"),"Geçerli ekran boyutu ve çözünürlük gir.");}
  const ppi=Math.sqrt(w*w+h*h)/size;
  const pitch=25.4/ppi;
  let label=ppi>=160?"Çok yüksek piksel yoğunluğu":ppi>=120?"Yüksek piksel yoğunluğu":ppi>=90?"Dengeli piksel yoğunluğu":"Düşük piksel yoğunluğu";
  show($("#ppiResult"),`<div class="result-grid">
    <div class="result-item"><small>PPI</small><b>${fmt(ppi,1)}</b></div>
    <div class="result-item"><small>Piksel aralığı</small><b>${fmt(pitch,3)} mm</b></div>
    <div class="result-item"><small>Yorum</small><b style="font-size:15px">${label}</b></div>
  </div>`);
});

function humanTime(sec){
  sec=Math.round(sec);
  const h=Math.floor(sec/3600), m=Math.floor((sec%3600)/60), s=sec%60;
  return [h?`${h} sa`:"",m?`${m} dk`:"",(!h&&s)?`${s} sn`:""].filter(Boolean).join(" ");
}
$("#calcDownload").addEventListener("click",()=>{
  const gb=parseFloat($("#dlSize").value), mbps=parseFloat($("#dlMbps").value), eff=parseFloat($("#dlEfficiency").value);
  if(!(gb>0&&mbps>0)){return show($("#dlResult"),"Geçerli dosya boyutu ve internet hızı gir.");}
  const seconds=(gb*8*1000)/(mbps*eff);
  const realMbps=mbps*eff;
  const mbpsBytes=realMbps/8;
  show($("#dlResult"),`<div class="result-grid">
    <div class="result-item"><small>Tahmini süre</small><b>${humanTime(seconds)}</b></div>
    <div class="result-item"><small>Efektif hız</small><b>${fmt(realMbps,1)} Mbps</b></div>
    <div class="result-item"><small>Yaklaşık aktarım</small><b>${fmt(mbpsBytes,1)} MB/s</b></div>
  </div><div class="sub">Sunucu limiti, Wi‑Fi ve disk yazma hızı süreyi değiştirebilir.</div>`);
});

$("#calcHz").addEventListener("click",()=>{
  const hz=parseFloat($("#hzValue").value);
  if(!(hz>0)){return show($("#hzResult"),"Geçerli bir Hz değeri gir.");}
  const ms=1000/hz;
  const vs60=(1000/60)-ms;
  show($("#hzResult"),`<div class="result-grid">
    <div class="result-item"><small>Yenileme hızı</small><b>${fmt(hz,0)} Hz</b></div>
    <div class="result-item"><small>Bir kare süresi</small><b>${fmt(ms,2)} ms</b></div>
    <div class="result-item"><small>60 Hz'e göre</small><b>${vs60>0?fmt(vs60,2)+" ms daha kısa":"—"}</b></div>
  </div><div class="sub">Bu yalnızca teorik yenileme aralığıdır; gerçek input latency sistem ve oyuna göre değişir.</div>`);
});

$("#year").textContent=new Date().getFullYear();
$("#calcSens").click();
