
(function(){
  const cfg = window.OYUNOPTI_CONFIG || {};
  const consentKey = "oyunopti_analytics_consent_v1";

  function loadGA(){
    const id=(cfg.GA_MEASUREMENT_ID||"").trim();
    if(!id || window.__oyunopti_ga_loaded) return;
    window.__oyunopti_ga_loaded=true;
    const s=document.createElement("script");
    s.async=true;
    s.src="https://www.googletagmanager.com/gtag/js?id="+encodeURIComponent(id);
    document.head.appendChild(s);
    window.dataLayer=window.dataLayer||[];
    window.gtag=function(){dataLayer.push(arguments)};
    gtag("js",new Date());
    gtag("config",id,{"anonymize_ip":true});
  }

  function consent(){
    if(!cfg.GA_MEASUREMENT_ID) return;
    const saved=localStorage.getItem(consentKey);
    if(saved==="yes"){ loadGA(); return; }
    if(saved==="no") return;

    const bar=document.createElement("div");
    bar.className="consent-bar";
    bar.innerHTML=`<div><b>İstatistik izni</b><span>Siteyi geliştirmek için isteğe bağlı anonim trafik ölçümü kullanabiliriz.</span></div>
      <div class="consent-actions"><button data-no>Reddet</button><button class="yes" data-yes>Kabul et</button></div>`;
    document.body.appendChild(bar);
    bar.querySelector("[data-yes]").onclick=()=>{localStorage.setItem(consentKey,"yes");bar.remove();loadGA()};
    bar.querySelector("[data-no]").onclick=()=>{localStorage.setItem(consentKey,"no");bar.remove()};
  }

  function affiliateCards(){
    document.querySelectorAll("[data-affiliate]").forEach(a=>{
      const key=a.getAttribute("data-affiliate");
      const url=cfg.AFFILIATE && cfg.AFFILIATE[key];
      if(url){
        a.href=url;
        a.target="_blank";
        a.rel="nofollow sponsored noopener";
        a.classList.remove("disabled");
        a.addEventListener("click",()=>{
          if(window.gtag) gtag("event","affiliate_click",{"item_category":key,"link_url":url});
        });
      } else {
        a.removeAttribute("href");
        a.classList.add("disabled");
        a.textContent="Affiliate linki eklenecek";
      }
    });
  }

  function trackTools(){
    document.querySelectorAll("button[id^='calc']").forEach(btn=>{
      btn.addEventListener("click",()=>{
        if(window.gtag) gtag("event","tool_use",{"tool":btn.id});
      });
    });
  }

  function sponsorEmail(){
    const mail=(cfg.CONTACT_EMAIL||"").trim();
    document.querySelectorAll("[data-contact]").forEach(el=>{
      if(mail){ el.href="mailto:"+mail; el.textContent=mail; }
      else { el.textContent="İletişim adresi yakında"; el.removeAttribute("href"); }
    });
  }

  document.addEventListener("DOMContentLoaded",()=>{
    consent();
    affiliateCards();
    trackTools();
    sponsorEmail();
  });
})();
