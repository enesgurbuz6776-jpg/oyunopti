"""OyunOpti FPS Booster Pro — conservative Windows tuning and manual FPS log."""
import csv, json, os, re, subprocess, sys, tkinter as tk, webbrowser, threading, time, math, hashlib, base64, binascii
from tkinter import messagebox, ttk, filedialog
from datetime import datetime, date, timezone, timedelta
from pathlib import Path
from collections import deque
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature

VERSION="1.1.0 Pro"
BASE=Path(os.environ.get("APPDATA",str(Path.home()))) / "OyunOptiFPSBooster"
FILE=BASE/"state.json"
LICENSE_FILE=BASE/"license.txt"
PUBLIC_KEY_B64="lFsWonl0lL6WBlf8bcGKcY0rIOvKj6CBC4wJ6fEclQc="
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


def device_code():
    """A one-way local device code. MachineGuid never leaves the computer."""
    if sys.platform != "win32":
        return "WINDOWS-REQUIRED"
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r"SOFTWARE\Microsoft\Cryptography",
                            0,winreg.KEY_READ | getattr(winreg,"KEY_WOW64_64KEY",0)) as handle:
            guid=str(winreg.QueryValueEx(handle,"MachineGuid")[0])
    except OSError:
        return "DEVICE-ID-UNAVAILABLE"
    return hashlib.sha256(("OyunOpti-Pro-Device-v1|"+guid).encode("utf-8")).hexdigest()[:32].upper()

def _unb64(value):
    return base64.urlsafe_b64decode(value+"="*((-len(value))%4))

def validate_license(token, machine=None, current=None):
    """Fail closed. Verify Ed25519 issuer signature, machine binding, and UTC expiry."""
    machine=device_code() if machine is None else machine
    if not machine or machine in ("WINDOWS-REQUIRED","DEVICE-ID-UNAVAILABLE"):
        raise ValueError("Bu bilgisayarda cihaz kodu okunamıyor.")
    token=(token or "").strip()
    if len(token)>4096:
        raise ValueError("Lisans anahtarı çok uzun.")
    try:
        segments=token.split(".")
        if len(segments)!=2:raise ValueError()
        payload_raw=_unb64(segments[0])
        signature=_unb64(segments[1])
        if len(payload_raw)>1024 or len(signature)!=64:raise ValueError()
        public=Ed25519PublicKey.from_public_bytes(base64.b64decode(PUBLIC_KEY_B64))
        public.verify(signature,payload_raw)
        data=json.loads(payload_raw.decode("utf-8"))
        if data.get("version")!=1 or data.get("plan")!="pro":raise ValueError()
        if data.get("device")!=machine:raise ValueError("Bu lisans farklı bir bilgisayar için.")
        expiry=date.fromisoformat(data["expires"])
        if expiry.year<2026 or expiry.year>2040:raise ValueError()
        now=current or datetime.now(timezone.utc).date()
        if now>expiry:raise ValueError("Lisansın süresi dolmuş. Yenileme gerekiyor.")
        return data
    except InvalidSignature:
        raise ValueError("Lisansın dijital imzası geçersiz.") from None
    except (ValueError,KeyError,TypeError,UnicodeError,json.JSONDecodeError,OverflowError,
            binascii.Error,AttributeError):
        raise ValueError("Lisans geçersiz, süresi dolmuş veya bu cihaza ait değil.") from None

def stored_license():
    try:return LICENSE_FILE.read_text(encoding="utf-8").strip()
    except OSError:return ""

class App(tk.Tk):
    def __init__(self):
        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("OyunOpti.FPSBooster")
            except (AttributeError, OSError):
                pass
        super().__init__()
        self.title("OyunOpti FPS Booster Pro")
        icon_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
        icon_file = icon_dir / "assets" / "oyunopti.ico"
        if icon_file.is_file():
            try:
                self.iconbitmap(default=str(icon_file))
            except tk.TclError:
                pass
        self.geometry("1120x780"); self.minsize(900,650); self.configure(bg=BG)
        self.data=load(); self.profile=tk.StringVar(value=self.data["profile"])
        self.license_data=None
        self.device_id=device_code()
        try:self.license_data=validate_license(stored_license(),self.device_id)
        except ValueError:pass
        self.license_status=tk.StringVar(value="Lisans doğrulanmadı.")
        self.mode=tk.BooleanVar(value=True); self.plan=tk.BooleanVar(value=False)
        self.before=tk.StringVar(); self.fps_after=tk.StringVar()
        self.low1=tk.StringVar(); self.low2=tk.StringVar()
        self.pm_binary=tk.StringVar(value="")
        self.pm_game=tk.StringVar(value="TslGame.exe")
        self.live_fps=tk.StringVar(value="— FPS")
        self.low_fps=tk.StringVar(value="—")
        self.monitor_state=tk.StringVar(value="FPS ölçümü kapalı. PresentMon CLI ile ölçüm için kullanılabilir.")
        self.pm_samples=deque(maxlen=2000)
        self.pm_process=None
        self.pm_last_frame=0
        self.pm_overlay=None
        self.pm_token=0
        self.protocol("WM_DELETE_WINDOW",self.shutdown)
        self.after(650,self.poll_monitor)
        nav=tk.Frame(self,bg=NAV,width=218); nav.pack(side="left",fill="y"); nav.pack_propagate(False)
        self.text(nav,"◇  OyunOpti",22,WHITE,True).pack(anchor="w",padx=16,pady=(32,4))
        self.text(nav,"PRO  /  LİSANSLI SÜRÜM",9,AQUA,True).pack(anchor="w",padx=20,pady=(0,24))
        tk.Frame(nav,bg=BORDER,height=1).pack(fill="x",padx=16,pady=(0,17))
        self.text(nav,"KONTROL MERKEZİ",9,BLUE,True).pack(anchor="w",padx=20,pady=(0,9))
        for p in ["Genel Bakış","FPS Ölçümü","Oyun Profilleri","Pro Optimizasyon","Canlı FPS Pro","Geri Al","Lisansım","OyunOpti Pro","Hakkında"]:
            tk.Button(nav,text=("  ✦  " if "Pro" in p else "  ◇  ")+p,anchor="w",bg=NAV,fg=PURPLE if "Pro" in p else WHITE,activebackground=PANEL,activeforeground=AQUA,
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
    def license_active(self):
        try:
            self.license_data=validate_license(stored_license(),self.device_id)
            return True
        except ValueError:
            self.license_data=None
            return False
    def require_license(self):
        if self.license_active():return True
        messagebox.showwarning("Pro lisans gerekli","Bu özelliği kullanabilmek için aktif OyunOpti Pro lisansı gerekiyor.")
        self.show("Lisansım")
        return False
    def show(self,p):
        if p not in ("Lisansım","Hakkında","Geri Al") and not self.license_active():
            p="Lisansım"
        {"Genel Bakış":self.home,"Pro Optimizasyon":self.opt,"Canlı FPS Pro":self.monitor_page,"Oyun Profilleri":self.profiles,
         "FPS Ölçümü":self.fps,"Geri Al":self.back,"Lisansım":self.activation,"OyunOpti Pro":self.pro,"Hakkında":self.about}[p]()
    def activation(self):
        f=self.page("OYUNOPTI PRO • LİSANS","Lisans Aktivasyonu",
            "OyunOpti'nin FPS ölçümü, optimizasyonu ve performans araçları aktif Pro lisansı gerektirir.")
        c=self.card(f)
        self.text(c,"CİHAZ KODUN",11,AQUA,True).pack(anchor="w")
        self.text(c,self.device_id,15,WHITE,True).pack(anchor="w",pady=(9,10))
        self.button(c,"Cihaz Kodunu Kopyala",lambda:self.copy_device()).pack(anchor="w",pady=(0,12))
        tk.Button(c,text="Pro Lisans Satın Al ↗",
                  command=lambda:webbrowser.open("https://oyunopti.com/pro-satin-al.html?device="+self.device_id),
                  bg="#554280",fg=WHITE,activebackground="#675297",relief="flat",
                  font=("Segoe UI",10,"bold"),padx=14,pady=10).pack(anchor="w",pady=(0,12))
        self.text(c,"Satın alma sonrasında cihaz koduna özel lisans verilir. Cihaz kodu kişisel dosya ya da ham Windows GUID değildir.",10,MUTED).pack(anchor="w")
        c=self.card(f)
        self.text(c,"PRO LİSANS ANAHTARI",11,AQUA,True).pack(anchor="w",pady=(0,9))
        self.license_entry=tk.Text(c,height=5,bg=BG,fg=WHITE,insertbackground=WHITE,wrap="word",
                                   font=("Consolas",10),relief="flat",padx=10,pady=10)
        self.license_entry.pack(fill="x",pady=(0,13))
        if self.license_active():
            self.text(c,"✓ Aktif Pro lisansı · Son gün: "+self.license_data["expires"],11,AQUA,True).pack(anchor="w",pady=(0,10))
        self.button(c,"Lisansı Doğrula ve Etkinleştir",self.activate).pack(anchor="w")
        c=self.card(f)
        self.text(c,"OYUNOPTI PRO · $10 / AY",16,WHITE,True).pack(anchor="w")
        self.text(c,"Ödeme onayından sonra lisans otomatik üretilir. Satış sayfası aktif değilse henüz ödeme alınmaz; bu ekrandan durumunu kontrol edebilirsin.",10,MUTED).pack(anchor="w",pady=(11,10))
        tk.Button(c,text="İletişim Sayfasını Aç ↗",command=lambda:webbrowser.open("https://oyunopti.com/iletisim.html"),
                  bg="#294569",fg=WHITE,relief="flat",font=("Segoe UI",10,"bold"),padx=15,pady=11).pack(anchor="w")
    def copy_device(self):
        self.clipboard_clear()
        self.clipboard_append(self.device_id)
        self.update()
        messagebox.showinfo("Kopyalandı","Cihaz kodu panoya kopyalandı.")
    def activate(self):
        token=self.license_entry.get("1.0","end").strip()
        try:data=validate_license(token,self.device_id)
        except ValueError as exc:
            messagebox.showerror("Lisans doğrulanamadı",str(exc))
            return
        try:
            BASE.mkdir(parents=True,exist_ok=True)
            temp=LICENSE_FILE.with_suffix(".tmp")
            temp.write_text(token,encoding="utf-8")
            os.replace(temp,LICENSE_FILE)
        except OSError as exc:
            messagebox.showerror("Kayıt hatası",str(exc))
            return
        self.license_data=data
        messagebox.showinfo("OyunOpti Pro Aktif","Lisans etkin. Geçerlilik sonu: "+data["expires"])
        self.show("Genel Bakış")
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
        self.button(actions,"Pro Optimizasyon →",lambda:self.show("Pro Optimizasyon")).pack(side="left",padx=(0,11))
        tk.Button(actions,text="FPS Testi Kaydet",command=lambda:self.show("FPS Ölçümü"),bg="#294569",fg=WHITE,
                  relief="flat",font=("Segoe UI",10,"bold"),padx=16,pady=12).pack(side="left")
        c=self.card(f)
        self.text(c,"DURUM ÖZETİ",11,BLUE,True).pack(anchor="w",pady=(0,11))
        self.text(c,"●  "+("Geri yükleme yedeği mevcut" if self.data["backup"] else "Bekleyen optimizasyon yok"),11,AQUA).pack(anchor="w",pady=6)
        self.text(c,f"●  Oyun profili: {self.profile.get()}",11,MUTED).pack(anchor="w",pady=6)
        self.text(c,"●  FPS değerleri kullanıcı tarafından girilir; otomatik ölçülmez.",11,MUTED).pack(anchor="w",pady=6)
        c=self.card(f)
        self.text(c,"✦  OYUNOPTI PRO • $10 / ay (hedef)",15,PURPLE,True).pack(anchor="w")
        self.text(c,"Gerçek FPS takibi, Pro optimizasyon ve detaylı raporlar. Aktif Pro lisansı gerekir. Abonelik ödemesi henüz sisteme bağlanmadı.",10,MUTED).pack(anchor="w",pady=(9,14))
        tk.Button(c,text="Pro Özelliklerini Gör →",command=lambda:self.show("OyunOpti Pro"),
                  bg="#564384",fg=WHITE,activebackground="#6b56a2",relief="flat",
                  font=("Segoe UI",10,"bold"),padx=15,pady=11).pack(anchor="w")
    def opt(self):
        f=self.page("✦ OYUNOPTI PRO • LİSANSLI","Gelişmiş optimizasyon",
                    "Yalnızca seçtiğin ayarlar değiştirilir ve orijinal değerleri önce kaydedilir.")
        c=self.card(f)
        self.text(c,"OYUNOPTI PRO • LİSANSLI OPTİMİZASYON",10,PURPLE,True).pack(anchor="w",pady=(0,10))
        self.text(c,"Seçtiğin Windows ayarlarını uygula; cihazına göre sonuç değişebilir.",10,MUTED).pack(anchor="w",pady=(0,14))
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
        if not self.require_license():return
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
        if not self.require_license():return
        self.data["profile"]=self.profile.get();save(self.data)
        messagebox.showinfo("Kaydedildi",self.profile.get()+" seçildi.")
    def fps(self):
        f=self.page("MANUEL ÖLÇÜM","FPS önce — sonra",
                    "Aynı grafik ayarları ve benzer oyun sahnesinde ölç. Aralıktan tahmini ortalama hesaplama.")
        c=self.card(f)
        self.text(c,"ÖLÇÜM FORMU • "+self.profile.get(),11,AQUA,True).pack(anchor="w",pady=(0,12))
        g=tk.Frame(c,bg=PANEL);g.pack(fill="x")
        for i,(title,var) in enumerate([
            ("ÖNCE — ORTALAMA FPS",self.before),("SONRA — ORTALAMA FPS",self.fps_after),
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
        if not self.require_license():return
        try:
            a=float(self.before.get().replace(",","."));b=float(self.fps_after.get().replace(",","."))
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
        if not self.require_license():return
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
        f=self.page("OYUNOPTI PRO • ÜYELİK","OyunOpti Pro",
            "Lisanslı performans yazılımı. FPS ve optimizasyon özelliklerine yalnızca geçerli lisansla erişilir.")
        c=self.card(f)
        self.text(c,"PRO ABONELİK",12,PURPLE,True).pack(anchor="w")
        self.text(c,"$10 / ay",29,WHITE,True).pack(anchor="w",pady=(8,8))
        self.text(c,"Ödeme bağlantısı ve otomatik üyelik sistemi henüz açılmadı. Aktif lisansı olanlar özellikleri kullanabilir.",11,MUTED).pack(anchor="w")
        c=self.card(f)
        for title,body in [
            ("CANLI FPS","PresentMon CLI üzerinden gerçek FPS ve yaklaşık %1 düşük kare hızı"),
            ("WINDOWS OPTİMİZASYONU","Geri alınabilir, açıkça belirtilmiş Windows ayarları"),
            ("PERFORMANS ANALİZİ","Manuel karşılaştırmalar, grafik, CSV ve oyun profilleri")]:
            self.text(c,"✦ "+title,12,AQUA,True).pack(anchor="w",pady=(9,3))
            self.text(c,body,10,MUTED).pack(anchor="w",pady=(0,12))
        self.button(f,"Lisansım",lambda:self.show("Lisansım")).pack(anchor="w",pady=10)
    def monitor_page(self):
        f=self.page("✦ OYUNOPTI PRO • CANLI FPS","Canlı FPS Göstergesi",
                    "Gerçek FPS takibi için Intel PresentMon konsol aracı gerekir. Bu özellik yalnızca aktif Pro lisansıyla kullanılabilir.")
        c=self.card(f)
        self.text(c,"FPS ÖLÇÜMÜ • PRESENTMON ENTEGRASYONU",11,PURPLE,True).pack(anchor="w")
        self.text(c,"PresentMon CLI sürümünü resmi kaynaktan indir ve aşağıdan EXE'yi göster.",10,MUTED).pack(anchor="w",pady=(10,4))
        tk.Button(c,text="Intel PresentMon Kaynağını Aç ↗",command=lambda:webbrowser.open("https://github.com/GameTechDev/PresentMon/releases"),
                  bg="#2A3B60",fg=WHITE,relief="flat",font=("Segoe UI",9,"bold"),padx=12,pady=8).pack(anchor="w",pady=8)
        row=tk.Frame(c,bg=PANEL);row.pack(fill="x",pady=5)
        tk.Entry(row,textvariable=self.pm_binary,state="readonly",readonlybackground="#0D1B30",fg=WHITE,
                 font=("Segoe UI",10),relief="flat").pack(side="left",fill="x",expand=True,ipady=10,padx=(0,8))
        tk.Button(row,text="EXE Seç",command=self.select_presentmon,bg="#294569",fg=WHITE,
                  relief="flat",font=("Segoe UI",9,"bold"),padx=14,pady=10).pack(side="left")
        self.text(c,"İZLENECEK OYUN İŞLEMİ",9,BLUE,True).pack(anchor="w",pady=(14,5))
        ttk.Combobox(c,textvariable=self.pm_game,values=[
            "TslGame.exe","cs2.exe","VALORANT-Win64-Shipping.exe",
            "r5apex.exe","FortniteClient-Win64-Shipping.exe"],width=36).pack(anchor="w")
        self.text(c,"Oyunu aç, doğru işlem adını seç; özellikle tam ekran modunda FPS penceresi görünmeyebilir.",10,MUTED).pack(anchor="w",pady=(12,8))
        stats=tk.Frame(c,bg="#0C192D",padx=15,pady=15);stats.pack(fill="x",pady=12)
        self.text(stats,"CANLI FPS • SON KARELER",10,BLUE,True).pack(anchor="w")
        tk.Label(stats,textvariable=self.live_fps,bg="#0C192D",fg=AQUA,
                 font=("Segoe UI",30,"bold")).pack(anchor="w")
        lows=tk.Frame(stats,bg="#0C192D");lows.pack(anchor="w")
        self.text(lows,"%1 LOW (TAHMİNİ): ",10,MUTED).pack(side="left")
        tk.Label(lows,textvariable=self.low_fps,bg="#0C192D",fg=WHITE,
                 font=("Segoe UI",10,"bold")).pack(side="left")
        actions=tk.Frame(c,bg=PANEL);actions.pack(anchor="w",pady=(8,12))
        self.button(actions,"Ölçümü Başlat",self.start_monitor).pack(side="left",padx=(0,9))
        tk.Button(actions,text="Durdur",command=self.stop_monitor,bg="#294569",fg=WHITE,relief="flat",
                  font=("Segoe UI",10,"bold"),padx=16,pady=12).pack(side="left",padx=(0,9))
        tk.Button(actions,text="FPS Penceresi",command=self.toggle_overlay,bg="#58447c",fg=WHITE,relief="flat",
                  font=("Segoe UI",10,"bold"),padx=12,pady=12).pack(side="left")
        label=tk.Label(c,textvariable=self.monitor_state,bg=PANEL,fg=MUTED,
                       font=("Segoe UI",10),wraplength=640,justify="left",anchor="w")
        label.pack(anchor="w")
        self.text(f,"Not: FPS tahmini kare sunum aralıklarından hesaplanır; gerçek oyun testi gerekir. Tam ekran overlay desteği oyuna göre değişir.",10,MUTED).pack(anchor="w",pady=10)
    def select_presentmon(self):
        path=filedialog.askopenfilename(title="Resmi PresentMon konsol EXE dosyasını seç",
                                       filetypes=[("EXE files","*.exe")])
        if path:self.pm_binary.set(path)
    def start_monitor(self):
        if not self.require_license():return
        if sys.platform!="win32":
            return messagebox.showerror("Windows gerekli","Canlı FPS ölçümü Windows üzerinde çalışır.")
        if self.pm_process and self.pm_process.poll() is None:
            return messagebox.showinfo("Çalışıyor","Ölçüm zaten çalışıyor.")
        binary=Path(self.pm_binary.get().strip())
        if not binary.is_file() or not (binary.name.lower().startswith("presentmon") and binary.suffix.lower()==".exe"):
            return messagebox.showerror("PresentMon bulunamadı","Resmi PresentMon konsol EXE dosyasını seç.")
        process_name=self.pm_game.get().strip()
        if not re.fullmatch(r"[A-Za-z0-9_.-]{3,100}\.exe",process_name,re.I):
            return messagebox.showerror("Oyun seç","Geçerli oyun EXE adı gir: örn. TslGame.exe")
        self.pm_token+=1
        token=self.pm_token
        self.pm_samples.clear()
        self.pm_last_frame=0
        self.live_fps.set("— FPS")
        self.low_fps.set("—")
        cmd=[str(binary),"--process_name",process_name,"--output_stdout","--no_console_stats","--exclude_dropped"]
        try:
            self.pm_process=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                                             text=True,encoding="utf-8-sig",errors="replace",bufsize=1,
                                             creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        except OSError as exc:
            return messagebox.showerror("Başlatılamadı",str(exc))
        self.monitor_state.set("Ölçüm başladı. Oyunu aç ve birkaç saniye bekle; sadece gerçek kareler gösterilir.")
        threading.Thread(target=self.read_presentmon,args=(self.pm_process,token),
                         daemon=True).start()
    def read_presentmon(self,process,token):
        index=None
        try:
            for line in process.stdout:
                if token!=self.pm_token:break
                try:fields=next(csv.reader([line]))
                except (csv.Error,StopIteration):continue
                if index is None:
                    for key in ("MsBetweenPresents","MsBetweenDisplayChange"):
                        if key in fields:
                            index=fields.index(key)
                            break
                    continue
                if len(fields)<=index:continue
                try:millis=float(fields[index])
                except (ValueError,TypeError):continue
                if math.isfinite(millis) and 0.5<millis<1000:
                    self.pm_samples.append((time.monotonic(),millis))
        except (OSError,ValueError):pass
    def poll_monitor(self):
        if self.pm_process and not self.license_active():
            self.stop_monitor()
        try:
            samples=list(self.pm_samples)
            current=time.monotonic()
            fresh=[v for when,v in samples[-500:] if current-when<3]
            if len(fresh)>4:
                tail=fresh[-180:]
                mean_ms=sum(tail)/len(tail)
                self.live_fps.set(f"{1000/mean_ms:.0f} FPS")
                if len(tail)>=100:
                    quantile=sorted(tail)[min(len(tail)-1,int(len(tail)*0.99))]
                    self.low_fps.set(f"{1000/quantile:.0f} FPS")
                else:self.low_fps.set("Yeterli veri yok")
            else:
                self.live_fps.set("— FPS")
                self.low_fps.set("—")
            if self.pm_process and self.pm_process.poll() is not None:
                self.pm_process=None
                self.monitor_state.set("Ölçüm sona erdi. FPS görünmediyse oyun işlemini, PresentMon sürümünü ve erişim izinlerini kontrol et.")
        finally:
            self.after(700,self.poll_monitor)
    def stop_monitor(self):
        self.pm_token+=1
        p=self.pm_process
        self.pm_process=None
        if p and p.poll() is None:
            try:p.terminate()
            except OSError:pass
        self.monitor_state.set("FPS ölçümü durduruldu.")
        self.live_fps.set("— FPS")
        self.low_fps.set("—")
    def toggle_overlay(self):
        if not self.require_license():return
        if self.pm_overlay and self.pm_overlay.winfo_exists():
            self.pm_overlay.destroy()
            self.pm_overlay=None
            return
        overlay=tk.Toplevel(self)
        overlay.overrideredirect(True)
        overlay.attributes("-topmost",True)
        try:overlay.attributes("-alpha",0.92)
        except tk.TclError:pass
        overlay.configure(bg="#071423")
        overlay.geometry("178x76+80+80")
        label=tk.Label(overlay,textvariable=self.live_fps,bg="#071423",fg=AQUA,
                       font=("Segoe UI",22,"bold"),padx=10,pady=6)
        label.pack()
        close=tk.Button(overlay,text="Kapat ×",bg="#071423",fg=MUTED,relief="flat",
                        command=lambda:self.toggle_overlay())
        close.pack()
        xy={}
        def press(e):
            xy["x"],xy["y"]=e.x_root-overlay.winfo_x(),e.y_root-overlay.winfo_y()
        def drag(e):
            overlay.geometry(f"+{e.x_root-xy.get('x',0)}+{e.y_root-xy.get('y',0)}")
        for item in (overlay,label):
            item.bind("<Button-1>",press)
            item.bind("<B1-Motion>",drag)
        self.pm_overlay=overlay
    def shutdown(self):
        self.stop_monitor()
        if self.pm_overlay:
            try:self.pm_overlay.destroy()
            except tk.TclError:pass
        self.destroy()
    def about(self):
        f=self.page("ŞEFFAF OPTİMİZASYON","Hakkında",f"OyunOpti FPS Booster {VERSION}")
        c=self.card(f)
        for s in ["✓ Windows Oyun Modu","✓ İsteğe bağlı Yüksek Performans güç planı",
                  "✓ Eski ayarların yedeği ve geri alma","✓ Manuel FPS kaydı ve karşılaştırma",
                  "✓ PresentMon CLI ile Pro canlı FPS takip","✕ Sahte FPS sayacı yok","✕ FPS artış garantisi yok","✕ Oyun dosyalarına müdahale yok"]:
            self.text(c,s,11,MUTED).pack(anchor="w",pady=7)

if __name__=="__main__":App().mainloop()
