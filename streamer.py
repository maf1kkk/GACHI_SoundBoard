import os, sys, json, random, threading, time, ctypes, ctypes.wintypes, subprocess, winreg, tempfile
from pathlib import Path
import customtkinter as ctk
import keyboard, mouse

if getattr(sys, 'frozen', False): BASE_DIR = Path(sys.executable).parent
else: BASE_DIR = Path(__file__).parent
SOUNDS_DIR = BASE_DIR / "sounds"
CONFIG_FILE = BASE_DIR / "streamer_config.json"

DEFAULT_CONFIG = {"theme":"light","volume":80,"timer_enabled":True,"timer_min":5,"timer_max":15,"autostart":False,"hotkey_mode":True,"sound_hotkeys":{},"output_device":"default","mic_mode":False,"mic_gain":200}

MCI = ctypes.WinDLL("winmm")
MCI.mciSendStringW.argtypes = [ctypes.wintypes.LPCWSTR, ctypes.wintypes.LPWSTR, ctypes.wintypes.UINT, ctypes.wintypes.HANDLE]
MCI.mciSendStringW.restype = ctypes.wintypes.DWORD
alias_counter = 0; alias_lock = threading.Lock()

LIGHT = {
    "bg": "#faf8f5", "bg2": "#ffffff", "bg3": "#f5f2ed",
    "accent": "#007b83", "accent_hover": "#00666d",
    "text": "#2d2a26", "muted": "#6b655d",
    "border": "#e8e0d8", "border_accent": "#d4ccc3",
    "success": "#2e7d32", "danger": "#c62828",
    "sound": ["#007b83","#5a8a8c","#8a6e8c","#b8864e"],
    "scrollbar": "#c4bcb3", "scrollbar_hover": "#a49c93",
}

DARK = {
    "bg": "#0a0a0a", "bg2": "#161616", "bg3": "#1e1e1e",
    "accent": "#00cc88", "accent_hover": "#00aa6e",
    "text": "#e0e0e0", "muted": "#888888",
    "border": "#2a2a2a", "border_accent": "#3a3a3a",
    "success": "#2e7d32", "danger": "#ef5350",
    "sound": ["#00cc88","#4ea8aa","#b388cc","#d4995e"],
    "scrollbar": "#3a3a3a", "scrollbar_hover": "#555555",
}

FONT_MAIN = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_HEADER = ("Segoe UI", 16, "bold")
FONT_SMALL = ("Segoe UI", 9)
FONT_BTN = ("Segoe UI", 9, "bold")

PRIORITY_KW = ["aagh","aah","ahh","augh","cum","spank","slap","orgasm","moan","yeah","fuck","shit","oh","ah","ugh","groan","scream","penetration","1a","2a","3a","4a","1ag"]

def sound_weight(p):
    n = Path(p).stem.lower()
    for k in PRIORITY_KW:
        if k in n: return 3
    return 1

FFMPEG = None
try:
    r = subprocess.run(["where","ffmpeg"],capture_output=True,text=True,timeout=5)
    if r.returncode==0 and r.stdout.strip(): FFMPEG = r.stdout.strip().split("\n")[0].strip()
except: pass
if not FFMPEG:
    for p in [r"C:\ProgramData\chocolatey\lib\ffmpeg\tools\ffmpeg\bin\ffmpeg.exe","ffmpeg.exe"]:
        if Path(p).exists(): FFMPEG = p; break

HAS_SD = False
if FFMPEG:
    try: import sounddevice as sd; import soundfile as sf; HAS_SD = True
    except: pass

WAV_CACHE = Path(tempfile.gettempdir())/"sndb_cache"
WAV_CACHE.mkdir(exist_ok=True)
SD_LOG = Path(tempfile.gettempdir())/"sndb_debug.log"

def log_sd(msg):
    try:
        with open(SD_LOG,"a",encoding="utf-8") as f: f.write(f"{msg}\n")
    except: pass

def list_output_devs():
    if not HAS_SD: return []
    try:
        seen=set(); out=[]
        for i,d in enumerate(sd.query_devices()):
            if d["max_output_channels"]>0:
                n=d["name"]
                key=n.strip().rstrip("C ")
                if key not in seen:
                    seen.add(key); out.append((i,n))
        return out
    except: return []

def find_cable():
    for i,n in list_output_devs():
        if "cable" in n.lower(): return n
    return None

def _to_wav(mp3):
    w = WAV_CACHE/(Path(mp3).stem+".wav")
    if w.exists(): return str(w)
    if not FFMPEG: return None
    try:
        subprocess.run([FFMPEG,"-i",str(mp3),"-y","-acodec","pcm_s16le","-ar","44100","-ac","2",str(w)],capture_output=True,timeout=30)
        return str(w) if w.exists() else None
    except: return None

_sd_stream_lock = threading.Lock()

def play_sound(fp, vol=80, device=None, gain=200):
    global alias_counter
    mvol = max(0,min(1000,vol*10))
    if device and HAS_SD:
        def _p():
            try:
                w = _to_wav(fp)
                if not w: return
                d, sr = sf.read(w)
                gf = max(0.5, min(5.0, gain/100)) * (vol/100)
                d = d * gf
                mx = float(abs(d).max()) or 1.0
                if mx > 1.0: d = d / mx
                for i,n in list_output_devs():
                    if n==device:
                        with _sd_stream_lock:
                            sd.stop(); sd.play(d, sr, device=i)
                        return
            except Exception as e:
                log_sd(f"ERR: {e}")
        threading.Thread(target=_p,daemon=True).start()
    with alias_lock:
        alias_counter+=1; a=f"p{alias_counter%99999}"
    def _m():
        try:
            MCI.mciSendStringW(f"close {a}",None,0,None)
            MCI.mciSendStringW(f'open "{Path(fp).resolve()}" alias {a}',None,0,None)
            MCI.mciSendStringW(f"set {a} volume {mvol}",None,0,None)
            MCI.mciSendStringW(f"play {a} wait",None,0,None)
            MCI.mciSendStringW(f"close {a}",None,0,None)
        except: pass
    threading.Thread(target=_m,daemon=True).start()

class Theme:
    def __init__(s, root, cfg):
        s.root = root
        s.cfg = cfg
        s.t = LIGHT if cfg.get("theme","light")=="light" else DARK

    def toggle(s):
        new_theme = "dark" if s.t is LIGHT else "light"
        s.cfg["theme"] = new_theme
        s.t = LIGHT if new_theme=="light" else DARK
        with open(CONFIG_FILE,"w",encoding="utf-8") as f:
            json.dump(s.cfg,f,indent=2,ensure_ascii=False)
        s._apply()

    def _apply(s):
        t = s.t
        ctk.set_appearance_mode("light" if t is LIGHT else "dark")
        theme_color = "green" if t is LIGHT else "green"
        s.root.configure(fg_color=t["bg"])
        for w in s.root.winfo_children():
            s._recolor(w)
        for w in s.settings_widgets if hasattr(s,"settings_widgets") else []:
            s._recolor(w)

    def _recolor(s, w):
        try:
            if hasattr(w,"configure"):
                cls = w.__class__.__name__
                if cls=="CTkFrame" or cls=="CTkScrollableFrame":
                    fg = w.cget("fg_color")
                    if fg and fg not in ("transparent","#0a0a0a","#0d0d0d","#141414","#faf8f5","#ffffff","#f5f2ed"):
                        try: w.configure(fg_color=s.t["bg2"])
                        except: pass
        except: pass



class SettingsWin(ctk.CTkToplevel):
    def __init__(s,parent,cfg,sounds,on_save,theme):
        super().__init__(parent)
        s.cfg=cfg; s.sounds=sounds; s.on_save=on_save; s.theme=theme; s._hook=None; s.listening=-1
        s.title("Settings"); s.geometry("560x640"); s.resizable(False,False)
        s.transient(parent); s.grab_set()
        s.configure(fg_color=theme.t["bg"])
        s._ui()

    def _ui(s):
        t = s.theme.t
        outer = ctk.CTkFrame(s, fg_color=t["bg2"], border_color=t["accent"], border_width=1)
        outer.pack(fill="both",expand=True,padx=8,pady=8)
        m=ctk.CTkScrollableFrame(outer,fg_color=t["bg2"],
            scrollbar_button_color=t["scrollbar"], scrollbar_button_hover_color=t["scrollbar_hover"])
        m.pack(fill="both",expand=True,padx=6,pady=6)
        ctk.CTkLabel(m,text="Hotkey Bindings",font=FONT_HEADER,text_color=t["accent"]).pack(anchor="w",pady=(0,8))
        f=ctk.CTkFrame(m,fg_color="transparent"); f.pack(fill="x")
        ctk.CTkLabel(f,text="Sound",font=FONT_BOLD,text_color=t["accent"],width=190,anchor="w").grid(row=0,column=0,padx=(0,8))
        ctk.CTkLabel(f,text="Key",font=FONT_BOLD,text_color=t["accent"],width=140,anchor="w").grid(row=0,column=1,padx=(0,8))
        s.entries=[]
        for i,snd in enumerate(s.sounds[:24]):
            nm=snd.stem[:18]
            if len(snd.stem)>18: nm+=".."
            ctk.CTkLabel(f,text=nm,font=FONT_MAIN,text_color=t["text"],width=190,anchor="w").grid(row=i+1,column=0,padx=(0,8),pady=1,sticky="w")
            hk=s.cfg["sound_hotkeys"].get(snd.name,"")
            e=ctk.CTkEntry(f,width=140,placeholder_text="click to bind",fg_color=t["bg3"],text_color=t["text"],border_color=t["border"],font=FONT_MAIN)
            e.insert(0,hk); e.grid(row=i+1,column=1,padx=(0,5),pady=1)
            e.bind("<Button-1>",lambda _,idx=i: s._start_listen(idx))
            s.entries.append(e)
            ctk.CTkButton(f,text="X",width=28,fg_color="transparent",hover_color=t["danger"],text_color=t["muted"],font=FONT_BOLD,command=lambda idx=i: s._clear(idx)).grid(row=i+1,column=2,pady=1)
        ctk.CTkLabel(m,text="click entry, then press key",font=FONT_SMALL,text_color=t["muted"]).pack(anchor="w")
        sep=ctk.CTkFrame(m,height=1,fg_color=t["border"]); sep.pack(fill="x",pady=10)
        ctk.CTkLabel(m,text="Output Device",font=FONT_HEADER,text_color=t["accent"]).pack(anchor="w")
        devs=list_output_devs()
        names=["default (speakers)"]
        for _,n in devs: names.append(n)
        if not HAS_SD: names=["default (speakers) - sd/ffmpeg required"]
        s.dev_var=ctk.StringVar(value=s.cfg.get("output_device","default"))
        dev_menu=ctk.CTkOptionMenu(m,values=names,variable=s.dev_var,fg_color=t["bg3"],button_color=t["accent"],button_hover_color=t["accent_hover"],text_color=t["text"],dropdown_fg_color=t["bg2"],dropdown_hover_color=t["bg3"],dropdown_text_color=t["text"],font=FONT_MAIN)
        dev_menu.pack(anchor="w",pady=4)
        s.mic_var=ctk.BooleanVar(value=s.cfg.get("mic_mode",False))
        mic_frame=ctk.CTkFrame(m,fg_color="transparent"); mic_frame.pack(fill="x",pady=4)
        sw=ctk.CTkSwitch(mic_frame,text="play through mic (discord)",variable=s.mic_var,fg_color=t["border"],progress_color=t["accent"],button_color=t["muted"],button_hover_color=t["accent"],font=FONT_MAIN)
        sw.pack(side="left")
        if not HAS_SD:
            ctk.CTkLabel(mic_frame,text="need ffmpeg + sounddevice",text_color=t["danger"],font=FONT_SMALL).pack(side="left",padx=10)
        if not FFMPEG:
            ctk.CTkLabel(m,text="ffmpeg not found - mic mode disabled",text_color=t["danger"],font=FONT_SMALL).pack(anchor="w")
        gframe=ctk.CTkFrame(m,fg_color="transparent"); gframe.pack(fill="x",pady=4)
        ctk.CTkLabel(gframe,text="mic gain:",font=FONT_MAIN,text_color=t["text"]).pack(side="left",padx=(0,5))
        s.gain_var=ctk.IntVar(value=s.cfg.get("mic_gain",200))
        gain_slider=ctk.CTkSlider(gframe,from_=50,to=500,width=200,variable=s.gain_var,fg_color=t["border"],button_color=t["accent"],button_hover_color=t["accent_hover"],progress_color=t["accent"])
        gain_slider.pack(side="left",padx=(0,5))
        s.gain_lbl=ctk.CTkLabel(gframe,text=f"{s.gain_var.get()}%",width=40,font=FONT_BOLD,text_color=t["accent"])
        s.gain_lbl.pack(side="left")
        gain_slider.configure(command=lambda v: s.gain_lbl.configure(text=f"{int(v)}%"))
        sep2=ctk.CTkFrame(m,height=1,fg_color=t["border"]); sep2.pack(fill="x",pady=10)
        ctk.CTkLabel(m,text="Timer",font=FONT_HEADER,text_color=t["accent"]).pack(anchor="w")
        r1=ctk.CTkFrame(m,fg_color="transparent"); r1.pack(fill="x")
        s.tv=ctk.BooleanVar(value=s.cfg["timer_enabled"])
        ctk.CTkSwitch(r1,text="enabled",variable=s.tv,fg_color=t["border"],progress_color=t["accent"],button_color=t["muted"],button_hover_color=t["accent"],font=FONT_MAIN).pack(side="left",padx=(0,15))
        ctk.CTkLabel(r1,text="every",font=FONT_MAIN,text_color=t["text"]).pack(side="left")
        s.tmin_v=ctk.StringVar(value=str(s.cfg["timer_min"]))
        ctk.CTkEntry(r1,width=50,textvariable=s.tmin_v,fg_color=t["bg3"],text_color=t["text"],border_color=t["border"],font=FONT_MAIN).pack(side="left",padx=5)
        ctk.CTkLabel(r1,text="to",font=FONT_MAIN,text_color=t["text"]).pack(side="left")
        s.tmax_v=ctk.StringVar(value=str(s.cfg["timer_max"]))
        ctk.CTkEntry(r1,width=50,textvariable=s.tmax_v,fg_color=t["bg3"],text_color=t["text"],border_color=t["border"],font=FONT_MAIN).pack(side="left",padx=5)
        ctk.CTkLabel(r1,text="minutes",font=FONT_MAIN,text_color=t["text"]).pack(side="left")
        sep3=ctk.CTkFrame(m,height=1,fg_color=t["border"]); sep3.pack(fill="x",pady=10)
        ctk.CTkLabel(m,text="Other",font=FONT_HEADER,text_color=t["accent"]).pack(anchor="w")
        s.asv=ctk.BooleanVar(value=s.cfg["autostart"])
        ctk.CTkSwitch(m,text="start with windows",variable=s.asv,fg_color=t["border"],progress_color=t["accent"],button_color=t["muted"],button_hover_color=t["accent"],font=FONT_MAIN).pack(anchor="w",pady=2)
        s.hmv=ctk.BooleanVar(value=s.cfg["hotkey_mode"])
        ctk.CTkSwitch(m,text="enable background hotkeys",variable=s.hmv,fg_color=t["border"],progress_color=t["accent"],button_color=t["muted"],button_hover_color=t["accent"],font=FONT_MAIN).pack(anchor="w",pady=2)
        bf=ctk.CTkFrame(s,fg_color=t["bg"]); bf.pack(fill="x",padx=8,pady=(0,8))
        ctk.CTkButton(bf,text="Save",fg_color=t["success"],text_color="#fff",font=FONT_BOLD,hover_color="#1b5e20",command=s._save).pack(side="right",padx=5)
        ctk.CTkButton(bf,text="Cancel",fg_color=t["bg3"],text_color=t["muted"],font=FONT_BOLD,border_color=t["border"],border_width=1,hover_color=t["danger"],command=s.destroy).pack(side="right")

    def _start_listen(s,idx):
        t = s.theme.t
        if s.listening>=0: s.entries[s.listening].configure(fg_color=t["bg3"])
        s.listening=idx; e=s.entries[idx]; e.delete(0,"end"); e.insert(0,"press a key..."); e.configure(fg_color=t["accent_hover"], text_color="#fff")
        s._hook=keyboard.hook(lambda ev,i=idx: s._capture(ev,i))

    def _capture(s,ev,idx):
        if s.listening==idx and ev.event_type=="down":
            try: keyboard.unhook(s._hook)
            except: pass
            s.after(0,lambda: s._set(idx,ev.name))

    def _set(s,idx,k):
        t = s.theme.t
        if s.listening==idx:
            e=s.entries[idx]; e.delete(0,"end"); e.insert(0,k); e.configure(fg_color=t["bg3"],text_color=t["text"]); s.listening=-1

    def _clear(s,idx):
        s.entries[idx].delete(0,"end")
        if s.listening==idx:
            s.listening=-1
            try: keyboard.unhook(s._hook)
            except: pass

    def _save(s):
        hk={}
        for i,snd in enumerate(s.sounds[:24]):
            v=s.entries[i].get().strip()
            if v: hk[snd.name]=v
        try: tmin=int(s.tmin_v.get()); tmax=int(s.tmax_v.get())
        except: tmin,tmax=5,15
        if tmin<1: tmin=1
        if tmax<tmin: tmax=tmin
        s.cfg["sound_hotkeys"]=hk; s.cfg["timer_enabled"]=s.tv.get()
        s.cfg["timer_min"]=tmin; s.cfg["timer_max"]=tmax
        s.cfg["autostart"]=s.asv.get(); s.cfg["hotkey_mode"]=s.hmv.get()
        s.cfg["mic_mode"]=s.mic_var.get()
        s.cfg["output_device"]=s.dev_var.get()
        s.cfg["mic_gain"]=s.gain_var.get()
        with open(CONFIG_FILE,"w",encoding="utf-8") as f: json.dump(s.cfg,f,indent=2,ensure_ascii=False)
        s.on_save(s.cfg); s.destroy()

class SoundBoardApp:
    def __init__(s):
        s.cfg={**DEFAULT_CONFIG}
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE,encoding="utf-8") as f: s.cfg={**s.cfg,**json.load(f)}
            except: pass
        s.sounds=sorted(SOUNDS_DIR.iterdir(),key=lambda x:x.stem.lower()) if SOUNDS_DIR.exists() else []
        s.vol=s.cfg["volume"]; s.timer_id=0; s.timer_active=False; s.hotkey_reg=False; s.buttons=[]
        s._setup_win(); s._build_ui(); s._reg_hk(); s._start_timer(); s._autostart()

    def _setup_win(s):
        ctk.set_appearance_mode("light" if s.cfg.get("theme","light")=="light" else "dark")
        s.root=ctk.CTk(); s.root.title("SoundBoard"); s.root.geometry("780x560"); s.root.minsize(680,440)
        t = LIGHT if s.cfg.get("theme","light")=="light" else DARK
        s.root.configure(fg_color=t["bg"])
        s.theme = Theme(s.root, s.cfg)

    def _build_ui(s):
        t = s.theme.t
        s.root.grid_columnconfigure(0,weight=1); s.root.grid_rowconfigure(0,weight=1)

        card = ctk.CTkFrame(s.root, fg_color=t["bg2"], border_color=t["border"], border_width=1, corner_radius=6)
        card.grid(row=0,column=0,padx=12,pady=12,sticky="nsew")
        card.grid_columnconfigure(0,weight=1); card.grid_rowconfigure(2,weight=1)

        h=ctk.CTkFrame(card,fg_color=t["bg2"],height=42, corner_radius=0)
        h.grid(row=0,column=0,padx=6,pady=(6,0),sticky="ew")
        h.grid_columnconfigure(0,weight=1)
        ctk.CTkLabel(h,text="SoundBoard",font=FONT_HEADER,text_color=t["accent"]).pack(side="left")
        s.mode_label=ctk.CTkLabel(h,text="",font=FONT_SMALL,text_color=t["accent"])
        s.mode_label.pack(side="right",padx=(0,8))
        s.timer_label=ctk.CTkLabel(h,text="",font=FONT_SMALL,text_color=t["muted"])
        s.timer_label.pack(side="right",padx=(0,8))

        ctk.CTkButton(h,text="\u2630",font=("Segoe UI",14),fg_color="transparent",text_color=t["muted"],
            hover_color=t["bg3"],width=32,height=28,command=s._settings).pack(side="right",padx=(0,4))
        s.theme_btn=ctk.CTkButton(h,text="\u263e",font=("Segoe UI",14),fg_color="transparent",text_color=t["muted"],
            hover_color=t["bg3"],width=32,height=28,command=s._toggle_theme)
        s.theme_btn.pack(side="right")

        sc=ctk.CTkScrollableFrame(card,fg_color=t["bg2"],
            scrollbar_button_color=t["scrollbar"], scrollbar_button_hover_color=t["scrollbar_hover"], corner_radius=0)
        sc.grid(row=2,column=0,padx=6,pady=4,sticky="nsew")
        g=ctk.CTkFrame(sc,fg_color="transparent"); g.pack(fill="both",expand=True)
        for i,snd in enumerate(s.sounds):
            r=i//4; c=i%4
            col = t["sound"][i % len(t["sound"])]
            nm=snd.stem[:18]
            if len(snd.stem)>18: nm+=".."
            b=ctk.CTkButton(g,text=nm,fg_color=t["bg3"],text_color=t["text"],
                hover_color=t["bg2"],font=FONT_BTN,
                border_color=col, border_width=1,
                width=125,height=44,anchor="center",
                command=lambda snd=snd: s._play(snd))
            b.sound_path = snd
            b.grid(row=r,column=c,padx=4,pady=4,sticky="ew")
            g.grid_columnconfigure(c,weight=1,uniform="b")
            s.buttons.append(b)

        cb=ctk.CTkFrame(card,fg_color=t["bg2"],height=44, corner_radius=0)
        cb.grid(row=3,column=0,padx=6,pady=(0,2),sticky="ew")
        cb.grid_columnconfigure(2,weight=1)
        ctk.CTkButton(cb,text="Random",width=80,height=28,fg_color=t["accent"],text_color="#fff",
            font=FONT_BOLD,hover_color=t["accent_hover"],command=s._random).grid(row=0,column=0,padx=(0,8))
        ctk.CTkLabel(cb,text="Vol",font=FONT_MAIN,text_color=t["muted"]).grid(row=0,column=1,padx=(0,5))
        s.slider=ctk.CTkSlider(cb,from_=0,to=100,width=100,fg_color=t["border"],
            button_color=t["accent"],button_hover_color=t["accent_hover"],progress_color=t["accent"],command=s._vol)
        s.slider.set(s.vol); s.slider.grid(row=0,column=2,padx=(0,8),sticky="ew")
        s.vol_lbl=ctk.CTkLabel(cb,text=f"{s.vol}%",width=32,font=FONT_BOLD,text_color=t["accent"])
        s.vol_lbl.grid(row=0,column=3,padx=(0,10))
        s.timer_sw=ctk.CTkSwitch(cb,text="Timer",font=FONT_SMALL,fg_color=t["border"],progress_color=t["accent"],
            button_color=t["muted"],button_hover_color=t["accent"],command=s._toggle_timer)
        s.timer_sw.grid(row=0,column=4)

        st=ctk.CTkFrame(card,fg_color=t["bg2"],height=20, corner_radius=0)
        st.grid(row=4,column=0,padx=6,pady=(0,6),sticky="ew")
        st.grid_columnconfigure(0,weight=1)
        s.status=ctk.CTkLabel(st,text="",font=FONT_SMALL,text_color=t["muted"],anchor="w")
        s.status.grid(row=0,column=0,sticky="w")
        s._update_status()

    def _toggle_theme(s):
        s.theme.toggle()
        t = s.theme.t
        s.root.configure(fg_color=t["bg"])
        s._rebuild_ui()

    def _rebuild_ui(s):
        for w in s.root.winfo_children():
            w.destroy()
        s.buttons=[]
        s._build_ui()

    def _blend(s, c1, c2, t):
        c1 = (int(c1[1:3],16), int(c1[3:5],16), int(c1[5:7],16))
        c2 = (int(c2[1:3],16), int(c2[3:5],16), int(c2[5:7],16))
        r = int(c1[0]*(1-t) + c2[0]*t)
        g = int(c1[1]*(1-t) + c2[1]*t)
        b = int(c1[2]*(1-t) + c2[2]*t)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _play(s,snd):
        dev = s.cfg.get("output_device") if s.cfg.get("output_device") != "default" and s.cfg.get("mic_mode") else None
        play_sound(str(snd),s.vol,dev,s.cfg.get("mic_gain",200))
        t = s.theme.t
        for b in s.buttons:
            if getattr(b, "sound_path", None) != snd:
                continue
            try:
                accent = b.cget("border_color")
                bg = t["bg3"]
                b.configure(fg_color=accent, text_color="#fff")
                s.root.after(50, lambda bb=b, a=accent, bg=bg: bb.configure(fg_color=s._blend(a, bg, 0.4), text_color=t["muted"]))
                s.root.after(110, lambda bb=b, a=accent, bg=bg: bb.configure(fg_color=s._blend(a, bg, 0.7), text_color=t["text"]))
                s.root.after(190, lambda bb=b, a=accent, bg=bg: bb.configure(fg_color=s._blend(a, bg, 0.9), text_color=t["text"]))
                s.root.after(280, lambda bb=b, bg=bg: bb.configure(fg_color=bg, text_color=t["text"]))
            except: pass
            break

    def _random(s):
        if not s.sounds: return
        weights=[sound_weight(x) for x in s.sounds]
        snd=random.choices(s.sounds,weights=weights,k=1)[0]; s._play(snd)

    def _vol(s,v):
        s.vol=int(v); s.vol_lbl.configure(text=f"{s.vol}%")
        s.cfg["volume"]=s.vol

    def _toggle_timer(s):
        s.cfg["timer_enabled"]=s.timer_sw.get()
        if s.cfg["timer_enabled"]: s._start_timer()
        else: s.timer_id+=1; s.timer_active=False

    def _start_timer(s):
        if not s.cfg["timer_enabled"] or not s.sounds: return
        s.timer_id+=1; s.timer_active=True; tid=s.timer_id
        def loop():
            while s.timer_active and s.timer_id==tid:
                interval=random.randint(s.cfg["timer_min"],s.cfg["timer_max"])
                rem=interval*60
                while rem>0 and s.timer_active and s.timer_id==tid:
                    if rem%30==0 or rem<10:
                        m=rem//60; sec=rem%60
                        txt=f"next in {m}m {sec}s" if m>0 else f"next in {sec}s"
                        s.root.after(0,lambda t=txt: s.timer_label.configure(text=t))
                    time.sleep(1); rem-=1
                if s.timer_active and s.timer_id==tid:
                    s.root.after(0,s._random); s.root.after(0,lambda: s.timer_label.configure(text=""))
        threading.Thread(target=loop,daemon=True).start()

    def _reg_hk(s):
        if not s.cfg["hotkey_mode"]: return
        cnt=0
        for snd_name,hk in s.cfg["sound_hotkeys"].items():
            if not hk: continue
            p=SOUNDS_DIR/snd_name
            if not p.exists(): continue
            try: keyboard.add_hotkey(hk,lambda pp=p: s._play(pp)); cnt+=1
            except: pass
        s.hotkey_reg=bool(cnt)
        s._update_status()

    def _autostart(s):
        if not s.cfg["autostart"]: return
        try:
            k=winreg.OpenKey(winreg.HKEY_CURRENT_USER,r"Software\Microsoft\Windows\CurrentVersion\Run",0,winreg.KEY_SET_VALUE)
            exe=sys.executable if getattr(sys,"frozen",False) else str(Path(__file__).resolve())
            winreg.SetValueEx(k,"SoundBoard",0,winreg.REG_SZ,f'"{exe}"'); winreg.CloseKey(k)
        except: pass

    def _update_status(s):
        hk=len(s.cfg["sound_hotkeys"]); sn=len(s.sounds); tm="timer on" if s.cfg["timer_enabled"] else "timer off"
        dev=s.cfg.get("output_device") if s.cfg.get("mic_mode") and s.cfg.get("output_device")!="default" else "speaker"
        s.status.configure(text=f"{sn} sounds | {hk} hotkeys | {tm} | output: {dev}")
        s.mode_label.configure(text="mic" if s.cfg.get("mic_mode") and s.cfg.get("output_device")!="default" else "")

    def _settings(s): SettingsWin(s.root,s.cfg,s.sounds,s._on_save,s.theme)

    def _on_save(s,cfg):
        s.cfg=cfg; s.vol=s.cfg["volume"]; s.slider.set(s.vol); s.vol_lbl.configure(text=f"{s.vol}%"); s._update_status()
        keyboard.remove_all_hotkeys(); s._reg_hk()
        s.timer_id+=1; s.timer_active=False
        if s.cfg["timer_enabled"]: s._start_timer()
        s.timer_sw.select() if s.cfg["timer_enabled"] else s.timer_sw.deselect()
        s._autostart()

    def run(s):
        s.root.protocol("WM_DELETE_WINDOW",s._close)
        s.root.mainloop()

    def _close(s):
        s.timer_active=False
        try: keyboard.remove_all_hotkeys()
        except: pass
        try: mouse.unhook_all()
        except: pass
        try: s.root.destroy()
        except: pass
        os._exit(0)

if __name__=="__main__":
    try:
        SoundBoardApp().run()
    except Exception as e:
        import traceback
        err_log = Path(tempfile.gettempdir())/"sndb_crash.log"
        with open(err_log,"w",encoding="utf-8") as f:
            f.write(f"{e}\n{traceback.format_exc()}")
