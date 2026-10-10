"""OyunOpti FPS Booster Beta — conservative Windows tuning and manual FPS log."""
import csv, json, os, re, subprocess, sys, tkinter as tk, webbrowser
from tkinter import messagebox, ttk, filedialog
from datetime import datetime
from pathlib import Path

VERSION="0.3.0-beta"
BASE=Path(os.environ.get("APPDATA",str(Path.home()))) / "OyunOptiFPSBooster"
FILE=BASE/"state.json"
REG_KEY=r"Software\Microsoft\GameBar"
REG_VALUE="AutoGameModeEnabled"
GUID=re.compile(r"\b[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}\b")
BG="#080e1b"; PANEL="#132540"; NAV="#0a1629"; WHITE="#f1f6ff"; AQUA="#1bd6bb"; MUTED="#a3b8d5"; PURPLE="#b495ff"; BLUE="#91bbff"; BORDER="#233b5d"

def load():
    try:
        d=json.loads(FILE.read_text(encoding="utf-8"))
        return {"backup":d.get("backup"),"history":d.get("history",[]),"profile":d.get("profile","PUBG")}
    except (OSError, ValueError, TypeError):
        return {"backup":None,"history":[],"profile":"PUBG"}

def save(d):
    BASE.mkdir(parents=True,exist_ok=True)
    temp=FILE.with_suffix(".tmp")
    temp.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding="utf-8")
    os.replace(temp,FILE)

def power(*args):
    p=subprocess.run(["powercfg",*args],capture_output=True,text=True,errors="replace",timeout=15,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
    if p.returncode: raise RuntimeError((p.stderr or p.stdout or "Güç planı değiştirilemedi").strip())
    return p.stdout

def current_plan():
    match=GUID.search(power("/getactivescheme"))
    if not match: raise RuntimeError("Etkin güç planı tespit edilemedi")
    return match.group(0)

def read_mode():
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,REG_KEY,0,winreg.KEY_READ) as k:
            value,kind=winreg.QueryValueEx(k,REG_VALUE)
            return {"exists":True,"value":value,"kind":kind}
    except FileNotFoundError: return {"exists":False}

def set_mode():
    import winreg
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER,REG_KEY,0,winreg.KEY_READ|winreg.KEY_WRITE) as k:
        winreg.SetValueEx(k,REG_VALUE,0,winreg.REG_DWORD,1)

def undo_mode(d):
    import winreg
    if d["exists"]:
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER,REG_KEY,0,winreg.KEY_READ|winreg.KEY_WRITE) as k:
            winreg.SetValueEx(k,REG_VALUE,0,d["kind"],d["value"])
    else:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,REG_KEY,0,winreg.KEY_SET_VALUE) as k:
                winreg.DeleteValue(k,REG_VALUE)
        except FileNotFoundError: pass

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("OyunOpti FPS Booster — Beta")
        self.geometry("1120x780"); self.minsize(900,650); self.configure(bg=BG)
        self.data=load(); self.profile=tk.StringVar(value=self.data["profile"])
        self.mode=tk.BooleanVar(value=True); self.plan=tk.BooleanVar(value=False)
        self.before=tk.StringVar(); self.after=tk.StringVar()
        self.low1=tk.StringVar(); self.low2=tk.StringVar()
        nav=tk.Frame(self,bg=NAV,width=218); nav.pack(side="left",fill="y"); nav.pack_propagate(False)
        self.text(nav,"◇  OyunOpti",22,WHITE,True).pack(anchor="w",padx=16,pady=(32,4))
        self.text(nav,"FPS BOOSTER  /  v0.3 BETA",9,AQUA,True).pack(anchor="w",padx=20,pady=(0,24))
        tk.Frame(nav,bg=BORDER,height=1).pack(fill="x",padx=16,pady=(0,17))
        self.text(nav,"KONTROL MERKEZİ",9,BLUE,True).pack(anchor="w",padx=20,pady=(0,9))
        for p in ["Genel Bakış","Optimizasyon","Oyun Profilleri","FPS Ölçümü","Geri Al","OyunOpti Pro","Hakkında"]:
            tk.Button(nav,text=("  ✦  " if p=="OyunOpti Pro" else "  ◇  ")+p,anchor="w",bg=NAV,fg=PURPLE if p=="OyunOpti Pro" else WHITE,activebackground=PANEL,activeforeground=AQUA,
                relief="flat",font=("Segoe UI",11,"bold"),pady=15,command=lambda page=p:self.show(page)).pack(fill="x",padx=6)
        right=tk.Frame(self,bg=BG);right.pack(side="right",fill="both",expand=True)
        scrollbar=tk.Scrollbar(right)
        scrollbar.pack(side="right",fill="y")
        self.viewport=tk.Canvas(right,bg=BG,highlightthickness=0,yscrollcommand=scrollbar.set)
        self.viewport.pack(side="left",fill="both",expand=True)
        scrollbar.configure(command=self.viewport.yview)
        self.content=tk.Frame(self.viewport,bg=BG)
        self.content_id=self.viewport.create_window((0,0),window=self.content,anchor="nw")
        self.content.bind("<Configure>",lambda e:self.viewport.configure(scrollregion=self.viewport.bbox("all")))
        self.viewport.bind("<Configure>",lambda e:self.viewport.itemconfigure(self.content_id,width=e.width))
        self.viewport.bind("<Enter>",lambda e:self.bind_all("<MouseWheel>",self.scroll_mouse))
        self.viewport.bind("<Leave>",lambda e:self.unbind_all("<MouseWheel>"))
        self.show("Genel Bakış")

    def scroll_mouse(self,event):
        self.viewport.yview_scroll(int(-event.delta/120),"units")
    def text(self,parent,value,size=11,color=WHITE,bold=False):
        return tk.Label(parent,text=value,bg=parent.cget("bg"),fg=color,
                        font=("Segoe UI",size,"bold" if bold else "normal"),justify="left",anchor="w")
    def button(self,parent,value,command):
        return tk.Button(parent,text=value,command=command,bg=AQUA,fg=BG,activebackground="#35efd1",
                         font=("Segoe UI",10,"bold"),relief="flat",padx=16,pady=12)
    def page(self,kicker,title,desc):
        for x in self.content.winfo_children():x.destroy()
        self.viewport.yview_moveto(0)
        f=tk.Frame(self.content,bg=BG,padx=30,pady=24);f.pack(fill="both",expand=True)
        self.text(f,"OYUNOPTI  /  WINDOWS OPTİMİZASYON",9,"#91bbff",True).pack(anchor="w")
        self.text(f,kicker,10,AQUA,True).pack(anchor="w",pady=(28,8))
        self.text(f,title,27,WHITE,True).pack(anchor="w")
        t=self.text(f,desc,10,MUTED);t.configure(wraplength=670);t.pack(anchor="w",pady=(12,18))
        return f
    def card(self,f):
        c=tk.Frame(f,bg=PANEL,padx=20,pady=18,highlightthickness=1,highlightbackground=BORDER);c.pack(fill="x",pady=8)
        return c
    def show(self,p):
        {"Genel Bakış":self.home,"Optimizasyon":self.opt,"Oyun Profilleri":self.profiles,
         "FPS Ölçümü":self.fps,"Geri Al":self.back,"OyunOpti Pro":self.pro,"Hakkında":self.about}[p]()
    def home(self):
        f=self.page("PERFORMANS MERKEZİ","OyunOpti FPS Booster","Oyun profilin, Windows ayarların ve gerçek FPS karşılaştırmaların tek kontrol panelinde.")
        summary=tk.Frame(f,bg=BG);summary.pack(fill="x",pady=(4,15))
        count=len(self.data["history"])
        last=self.data["history"][-1] if count else None
        change=f'{float(last["change"]):+.2f}%' if last else "—"
        for title,value,tint in [("AKTİF OYUN",self.profile.get(),BLUE),("KAYITLI TEST",str(count),WHITE),("SON TEST DEĞİŞİMİ",change,AQUA)]:
            item=tk.Frame(summary,bg=PANEL,padx=16,pady=16,highlightthickness=1,highlightbackground=BORDER)
            item.pack(side="left",fill="both",expand=True,padx=(0,9))
            self.text(item,title,9,MUTED,True).pack(anchor="w")
            self.text(item,value,18,tint,True).pack(anchor="w",pady=(10,0))
        c=self.card(f)
        self.text(c,"⚡  TEK TIKLA GÜVENLİ OPTİMİZASYON",12,AQUA,True).pack(anchor="w")
        self.text(c,"Oyun Modu ve isteğe bağlı güç planı ayarlarını kontrol et.",13,WHITE,True).pack(anchor="w",pady=(15,6))
        self.text(c,"Oyun dosyalarını değiştirmez. FPS artışı garanti edilmez. Ayarlar geri alınabilir.",10,MUTED).pack(anchor="w",pady=(0,16))
        actions=tk.Frame(c,bg=PANEL);actions.pack(anchor="w")
        self.button(actions,"Optimizasyona Git →",lambda:self.show("Optimizasyon")).pack(side="left",padx=(0,11))
        tk.Button(actions,text="FPS Testi Kaydet",command=lambda:self.show("FPS Ölçümü"),bg="#294569",fg=WHITE,
                  relief="flat",font=("Segoe UI",10,"bold"),padx=16,pady=12).pack(side="left")
        c=self.card(f)
        self.text(c,"DURUM ÖZETİ",11,BLUE,True).pack(anchor="w",pady=(0,11))
        self.text(c,"●  "+("Geri yükleme yedeği mevcut" if self.data["backup"] else "Bekleyen optimizasyon yok"),11,AQUA).pack(anchor="w",pady=6)
        self.text(c,f"●  Oyun profili: {self.profile.get()}",11,MUTED).pack(anchor="w",pady=6)
        self.text(c,"●  FPS değerleri kullanıcı tarafından girilir; otomatik ölçülmez.",11,MUTED).pack(anchor="w",pady=6)
        c=self.card(f)
        self.text(c,"✦  OYUNOPTI PRO",15,PURPLE,True).pack(anchor="w")
        self.text(c,"Gelişmiş analiz, otomatik ölçüm ve oyun profilleri için planlanan özelliklere göz at.",10,MUTED).pack(anchor="w",pady=(9,14))
        tk.Button(c,text="Pro Özelliklerini Gör →",command=lambda:self.show("OyunOpti Pro"),
                  bg="#564384",fg=WHITE,activebackground="#6b56a2",relief="flat",
                  font=("Segoe UI",10,"bold"),padx=15,pady=11).pack(anchor="w")
    def opt(self):
        f=self.page("GÜVENLİ VE GERİ ALINABİLİR","Windows optimizasyonu",
                    "Yalnızca seçtiğin ayarlar değiştirilir ve orijinal değerleri önce kaydedilir.")
        c=self.card(f)
        self.text(c,"DEĞİŞTİRİLECEK AYARLAR",11,AQUA,True).pack(anchor="w",pady=(0,12))
        for var,title,note in [(self.mode,"Windows Oyun Modu → Açık","Mevcutsa açılır; zaten açıksa değişmez."),
                               (self.plan,"Güç Planı → Yüksek Performans","Elektrik tüketimi ve sıcaklık artabilir; mevcut plan gereklidir.")]:
            item=tk.Frame(c,bg="#192a49",padx=10,pady=11);item.pack(fill="x",pady=5)
            tk.Checkbutton(item,text=title,variable=var,bg="#192a49",fg=WHITE,selectcolor=BG,
                           activebackground="#192a49",activeforeground=WHITE,font=("Segoe UI",11,"bold")).pack(anchor="w")
            self.text(item,note,10,MUTED).pack(anchor="w",pady=(5,0))
        self.text(c,"FPS artışı garanti edilmez; oyun içinde tekrar ölç.",10,MUTED).pack(anchor="w",pady=(15,12))
        self.button(c,"Seçilenleri Uygula",self.apply).pack(anchor="w")
    def apply(self):
        if sys.platform!="win32":return messagebox.showerror("Hata","Windows 10/11 gereklidir.")
        if self.data["backup"]:return messagebox.showinfo("Yedek var","Yeni işlem için önce Geri Al kullan.")
        if not(self.mode.get() or self.plan.get()):return messagebox.showinfo("Seçim yok","En az bir ayar seç.")
        if not messagebox.askyesno("Onay","Seçili Windows ayarları değiştirilsin mi?"):return
        backup={}
        try:
            if self.mode.get():backup["mode"]=read_mode()
            if self.plan.get():backup["plan"]=current_plan()
            self.data["backup"]=backup;save(self.data)
            if self.mode.get():set_mode()
            if self.plan.get():power("/setactive","SCHEME_MIN")
            messagebox.showinfo("Tamam","Ayarlar uygulandı. Geri Al menüsünden dönebilirsin.")
        except Exception as e:
            messagebox.showerror("İşlem başarısız",str(e)+"\nOrijinal ayarlar geri alınabilir.")
        self.show("Genel Bakış")
    def profiles(self):
        f=self.page("OYUN PROFİLLERİ","Oyununu seç","Profil FPS sonuçlarını etiketlemek içindir.")
        c=self.card(f)
        ttk.Combobox(c,textvariable=self.profile,state="readonly",width=34,values=[
            "PUBG","CS2","Valorant","Apex Legends","Fortnite","Diğer"]).pack(anchor="w",pady=(0,18))
        self.button(c,"Profili Kaydet",self.saveprofile).pack(anchor="w")
    def saveprofile(self):
        self.data["profile"]=self.profile.get();save(self.data)
        messagebox.showinfo("Kaydedildi",self.profile.get()+" seçildi.")
    def fps(self):
        f=self.page("MANUEL ÖLÇÜM","FPS önce — sonra",
                    "Aynı grafik ayarları ve benzer oyun sahnesinde ölç. Aralıktan tahmini ortalama hesaplama.")
        c=self.card(f)
        self.text(c,"ÖLÇÜM FORMU • "+self.profile.get(),11,AQUA,True).pack(anchor="w",pady=(0,12))
        g=tk.Frame(c,bg=PANEL);g.pack(fill="x")
        for i,(title,var) in enumerate([
            ("ÖNCE — ORTALAMA FPS",self.before),("SONRA — ORTALAMA FPS",self.after),
            ("ÖNCE — %1 DÜŞÜK (opsiyonel)",self.low1),("SONRA — %1 DÜŞÜK (opsiyonel)",self.low2)]):
            box=tk.Frame(g,bg=PANEL);box.grid(row=i//2,column=i%2,sticky="ew",padx=4,pady=7)
            self.text(box,title,9,MUTED,True).pack(anchor="w",pady=(0,5))
            tk.Entry(box,textvariable=var,bg=BG,fg=WHITE,insertbackground=WHITE,
                     font=("Segoe UI",12),relief="flat").pack(fill="x",ipady=10)
        g.columnconfigure(0,weight=1);g.columnconfigure(1,weight=1)
        self.button(c,"Hesapla ve Kaydet",self.record).pack(anchor="w",pady=(18,0))
        self.text(f,"SON ÖLÇÜMLER",11,AQUA,True).pack(anchor="w",pady=(18,7))
        if self.data["history"]:
            self.button(f,"CSV Raporunu Dışa Aktar",self.export_csv).pack(anchor="w",pady=(4,10))
            self.draw_history(f)
        for r in self.data["history"][-4:][::-1]:
            self.text(f,f"{r['profile']} • {r['date']}    {r['before']:g} → {r['after']:g} FPS    {r['change']:+.2f}%",10).pack(anchor="w",pady=4)
    def record(self):
        try:
            a=float(self.before.get().replace(",","."));b=float(self.after.get().replace(",","."))
            if not(0<a<=10000 and 0<b<=10000):raise ValueError()
            lo1=self.low1.get().strip();lo2=self.low2.get().strip()
            if bool(lo1)!=bool(lo2):raise ValueError()
            if lo1:
                x=float(lo1.replace(",","."));y=float(lo2.replace(",","."))
                if not(0<x<=a and 0<y<=b):raise ValueError()
        except ValueError:
            return messagebox.showerror("Hatalı değer","Geçerli FPS sayıları gir. %1 düşük kutuları ikisi birden doldurulmalıdır.")
        delta=(b/a-1)*100
        self.data["history"].append({"profile":self.profile.get(),"date":datetime.now().strftime("%Y-%m-%d %H:%M"),
            "before":a,"after":b,"change":delta})
        self.data["history"]=self.data["history"][-100:];save(self.data)
        messagebox.showinfo("Kaydedildi",f"Girilen değerlere göre değişim: {delta:+.2f}%\nBu ölçüm gerçek bir hızlanma kanıtı değildir.")
        self.show("FPS Ölçümü")
    def back(self):
        f=self.page("AYARLARI GERİ YÜKLE","Geri Al","Orijinal Windows ayarlarını geri yükle.")
        c=self.card(f)
        if self.data["backup"]:self.button(c,"Orijinal Ayarları Geri Yükle",self.rollback).pack(anchor="w")
        else:self.text(c,"Geri alınacak kayıt bulunmuyor.",12,MUTED).pack(anchor="w")
    def rollback(self):
        if sys.platform!="win32":return messagebox.showerror("Hata","Windows gereklidir.")
        if not messagebox.askyesno("Onay","Orijinal ayarlara dönülsün mü?"):return
        d=self.data["backup"] or {};left=dict(d);errors=[]
        if "mode" in d:
            try:undo_mode(d["mode"]);del left["mode"]
            except Exception as e:errors.append(str(e))
        if "plan" in d:
            try:power("/setactive",d["plan"]);del left["plan"]
            except Exception as e:errors.append(str(e))
        self.data["backup"]=left or None;save(self.data)
        if errors:messagebox.showerror("Kısmi hata","\n".join(errors))
        else:messagebox.showinfo("Tamam","Orijinal ayarlar geri yüklendi.")
        self.show("Geri Al")
    def draw_history(self,f):
        rows=self.data["history"][-12:]
        values=[]
        for r in rows:
            try:values.append(float(r["change"]))
            except (ValueError,KeyError,TypeError):continue
        if not values:return
        c=self.card(f)
        self.text(c,"PERFORMANS DEĞİŞİM GRAFİĞİ • SON 12 TEST",10,BLUE,True).pack(anchor="w",pady=(0,10))
        chart=tk.Canvas(c,height=155,bg=PANEL,highlightthickness=0)
        chart.pack(fill="x")
        def paint(event=None):
            chart.delete("all")
            w=max(240,chart.winfo_width())
            left,right,top,bottom=38,w-18,18,133
            minimum=min(0,min(values))-2
            maximum=max(0,max(values))+2
            def yy(v):return top+(maximum-v)/(maximum-minimum)*(bottom-top)
            zero=yy(0)
            chart.create_line(left,zero,right,zero,fill="#3D5475",dash=(4,4))
            chart.create_text(30,zero,text="0%",fill=MUTED,anchor="e",font=("Segoe UI",9))
            pts=[]
            for i,v in enumerate(values):
                x=left+(right-left)*i/max(1,len(values)-1)
                pts.append((x,yy(v)))
            if len(pts)>1:
                chart.create_line(*[a for pair in pts for a in pair],fill=AQUA,width=2)
            for x,y in pts:
                chart.create_oval(x-4,y-4,x+4,y+4,fill=AQUA,outline=PANEL)
        chart.bind("<Configure>",paint)
    def export_csv(self):
        if not self.data["history"]:return messagebox.showinfo("Bilgi","Önce FPS ölçümü kaydet.")
        path=filedialog.asksaveasfilename(defaultextension=".csv",initialfile="oyunopti-fps-raporu.csv",
                                          filetypes=[("CSV dosyası","*.csv")])
        if not path:return
        fields=["date","profile","before","after","change"]
        try:
            with open(path,"w",encoding="utf-8-sig",newline="") as fp:
                writer=csv.DictWriter(fp,fieldnames=fields,extrasaction="ignore")
                writer.writeheader()
                for entry in self.data["history"]:
                    safe={k: ("'"+str(entry.get(k,"")) if str(entry.get(k,"")).startswith(("=","+","-","@")) and k in ("profile","date") else entry.get(k,"")) for k in fields}
                    writer.writerow(safe)
            messagebox.showinfo("Tamam","FPS ölçüm raporu kaydedildi.")
        except OSError as exc:messagebox.showerror("Hata",str(exc))
    def pro(self):
        f=self.page("✦ PRO / ERKEN TANITIM","OyunOpti Pro",
            "Daha gelişmiş analiz özellikleri için yol haritamız. Pro şu anda satışta değil; ödeme veya abonelik alınmıyor.")
        hero=tk.Frame(f,bg="#211d39",padx=22,pady=22,highlightthickness=1,highlightbackground="#514776")
        hero.pack(fill="x",pady=9)
        self.text(hero,"✦  OYUNOPTI PRO  •  YAKINDA",13,PURPLE,True).pack(anchor="w")
        self.text(hero,"Daha güçlü performans analizleri",20,WHITE,True).pack(anchor="w",pady=(15,10))
        self.text(hero,"Henüz Pro lisans ve ödeme sistemi yok. Bu ekrandaki gelişmiş özellikler planlama aşamasındadır.",10,"#C5B5E7").pack(anchor="w")
        c=self.card(f)
        self.text(c,"ÜCRETSİZ • ŞU ANDA AKTİF",12,AQUA,True).pack(anchor="w",pady=(0,12))
        for title in ["✓ Windows Oyun Modu ve isteğe bağlı güç planı","✓ Manuel FPS önce / sonra karşılaştırma",
                      "✓ Performans geçmişi grafiği ve CSV rapor","✓ Windows ayarlarını geri alma"]:
            self.text(c,title,11,WHITE).pack(anchor="w",pady=8)
        c=self.card(f)
        self.text(c,"PRO • PLANLANAN ÖZELLİKLER",12,PURPLE,True).pack(anchor="w",pady=(0,12))
        planned=[
          ("Otomatik FPS ölçümü","Güvenilir ölçüm araçlarıyla veri toplama entegrasyonu"),
          ("Gelişmiş kare süresi analizi","%1 düşük FPS ve kare süresi istatistikleri"),
          ("Oyuna özel optimizasyon profilleri","Şeffaf, test edilebilir ve geri alınabilir öneriler"),
          ("Ayrıntılı performans raporları","Uzun süreli ölçüm geçmişi ve karşılaştırmalar")]
        for title,desc in planned:
            item=tk.Frame(c,bg="#192941",padx=13,pady=11);item.pack(fill="x",pady=5)
            self.text(item,"✦ "+title+"  [PLANLANIYOR]",11,PURPLE,True).pack(anchor="w")
            self.text(item,desc,10,MUTED).pack(anchor="w",pady=(5,0))
        self.text(f,"Pro özellikleri hazır olmadığı için herhangi bir satın alma veya aktivasyon butonu bulunmaz.",10,MUTED).pack(anchor="w",pady=10)
    def about(self):
        f=self.page("ŞEFFAF OPTİMİZASYON","Hakkında",f"OyunOpti FPS Booster {VERSION}")
        c=self.card(f)
        for s in ["✓ Windows Oyun Modu","✓ İsteğe bağlı Yüksek Performans güç planı",
                  "✓ Eski ayarların yedeği ve geri alma","✓ Manuel FPS kaydı ve karşılaştırma",
                  "✕ Sahte FPS sayacı yok","✕ FPS artış garantisi yok","✕ Oyun dosyalarına müdahale yok"]:
            self.text(c,s,11,MUTED).pack(anchor="w",pady=7)

if __name__=="__main__":App().mainloop()
