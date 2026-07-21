import os
import sys
import random
import json
import threading
import time
import ctypes
import ctypes.wintypes
from pathlib import Path

import keyboard
import mouse
import pystray
from PIL import Image, ImageDraw

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent
SOUNDS_DIR = BASE_DIR / "sounds"
CONFIG_FILE = BASE_DIR / "config.json"

DEFAULT_CONFIG = {
    "hotkeys": [
        "space", "ctrl", "alt", "shift",
        "w","a","s","d","q","e","r","t","y",
        "f","g","h","j","k","l",
        "z","x","c","v","b","n","m",
        "1","2","3","4","5","6","7","8","9","0"
    ],
    "mouse_buttons": ["left", "right", "middle", "x1", "x2"],
    "volume": 100,
    "cooldown_ms": 300,
    "tray_icon": True
}

winmm = ctypes.WinDLL("winmm")
winmm.mciSendStringW.argtypes = [ctypes.wintypes.LPCWSTR, ctypes.wintypes.LPWSTR, ctypes.wintypes.UINT, ctypes.wintypes.HANDLE]
winmm.mciSendStringW.restype = ctypes.wintypes.DWORD

alias_counter = 0
alias_lock = threading.Lock()

def play_sound(filepath):
    global alias_counter
    with alias_lock:
        alias_counter += 1
        alias = f"p{alias_counter % 99999}"

    def _play():
        try:
            winmm.mciSendStringW(f"close {alias}", None, 0, None)
            fp = str(Path(filepath).resolve())
            winmm.mciSendStringW(f'open "{fp}" alias {alias}', None, 0, None)
            winmm.mciSendStringW(f"play {alias} wait", None, 0, None)
            winmm.mciSendStringW(f"close {alias}", None, 0, None)
        except Exception:
            pass

    threading.Thread(target=_play, daemon=True).start()

PRIORITY_KEYWORDS = [
    "aagh", "aah", "ahh", "augh", "cum", "spank", "slap", "orgasm",
    "moan", "yeah", "fuck", "shit", "oh", "ah", "ugh", "groan",
    "scream", "penetration", "1a", "2a", "3a", "4a", "1ag"
]

def sound_weight(path):
    name = Path(path).stem.lower()
    for kw in PRIORITY_KEYWORDS:
        if kw in name:
            return 3
    return 1

def load_sounds():
    if not SOUNDS_DIR.exists():
        SOUNDS_DIR.mkdir(parents=True, exist_ok=True)
    return [str(f) for f in SOUNDS_DIR.iterdir() if f.suffix.lower() in (".mp3", ".wav", ".ogg", ".flac", ".m4a")]

def load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                return {**DEFAULT_CONFIG, **json.load(f)}
        except Exception:
            pass
    return dict(DEFAULT_CONFIG)

def create_tray_icon(on_exit):
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([16, 16, 48, 48], fill=(80, 140, 255, 220))
    draw.ellipse([24, 24, 40, 40], fill=(200, 220, 255, 180))
    menu = pystray.Menu(
        pystray.MenuItem("Sounds folder", lambda: os.startfile(str(SOUNDS_DIR))),
        pystray.MenuItem("Exit", on_exit)
    )
    return pystray.Icon("sndsrv_test", img, "Audio Service [TEST]", menu)

class TestApp:
    def __init__(self):
        self.config = load_config()
        self.sounds = load_sounds()
        self.running = True
        self.last_play = 0.0

        if not self.sounds:
            print("No sounds found in:", SOUNDS_DIR)

        self.register_hotkeys()
        self.register_mouse()

    def play_random(self):
        now = time.time()
        if (now - self.last_play) * 1000 < self.config.get("cooldown_ms", 300):
            return
        self.last_play = now
        if not self.sounds:
            self.sounds = load_sounds()
            if not self.sounds:
                return
        weights = [sound_weight(s) for s in self.sounds]
        s = random.choices(self.sounds, weights=weights, k=1)[0]
        play_sound(s)

    def register_hotkeys(self):
        for hk in self.config.get("hotkeys", []):
            try:
                keyboard.add_hotkey(hk, lambda k=hk: self.play_random())
            except Exception:
                pass

    def register_mouse(self):
        btn_map = {
            "left": mouse.LEFT, "right": mouse.RIGHT,
            "middle": mouse.MIDDLE, "x1": mouse.X, "x2": mouse.X2
        }
        btns = [btn_map[b] for b in self.config.get("mouse_buttons", []) if b in btn_map]
        if btns:
            try:
                mouse.on_button(lambda: self.play_random(), buttons=tuple(btns), types=(mouse.DOWN,))
            except Exception:
                pass

    def exit_app(self, icon=None):
        self.running = False
        if icon:
            icon.stop()
        keyboard.unhook_all()
        mouse.unhook_all()

    def run(self):
        print("=== SoundPrank TEST MODE ===")
        print(f"Sounds loaded: {len(self.sounds)}")
        print(f"Hotkeys: {', '.join(self.config.get('hotkeys', []))}")
        print(f"Mouse buttons: {', '.join(self.config.get('mouse_buttons', []))}")
        print("Tray icon running. Right-click to exit.")
        print("Secret exit: press Ctrl+Alt+Shift+F12\n")

        try:
            keyboard.add_hotkey("ctrl+alt+shift+f12", self.exit_app)
        except Exception:
            pass

        if self.config.get("tray_icon", True):
            icon = create_tray_icon(self.exit_app)
            icon.run()
        else:
            try:
                while self.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.exit_app()

if __name__ == "__main__":
    app = TestApp()
    app.run()
