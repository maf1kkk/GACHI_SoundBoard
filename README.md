# 🎙️ GACHI SoundBoard — Streamer Soundboard

> **Soundpad for streamers.** Weighted random GachiMuchi sounds, hotkey bindings, timer, and simultaneous output to speakers + Discord/voice chat via VB-CABLE.

![SoundBoard](screenshot.png)

## ✨ Features

- **300+ GachiMuchi sounds** — weighted random (short/funny sounds 3× more likely)
- **Soundpad-style mic injection** — plays through speakers AND your Discord microphone simultaneously via [VB-CABLE](https://vb-audio.com/Cable/)
- **OBS-ready** — capture as separate audio source (Audio Input Capture → `CABLE Output`)
- **Hotkey bindings** — bind any key to any sound, works in background
- **Random timer** — auto-plays sounds at configurable intervals
- **Sound samples** — 20+ short sounds included (<5s each)
- **Dark theme** — customtkinter modern UI

## 🚀 Quick Start

### For streaming (Discord + OBS viewers):

1. Install [VB-CABLE](https://vb-audio.com/Cable/) (free virtual audio driver)
2. Download `SoundBoard.exe` from Releases, put it with `sounds/` folder
3. **In SoundBoard** → Settings → select `CABLE Input` as Output Device → enable "Play through microphone"
4. **In Discord** → Voice & Video → Input Device → `CABLE Output` (set once, friends hear sounds)
5. **In OBS** → add Audio Input Capture → `CABLE Output` → route to "Stream" only → viewers hear sounds separately
6. You hear sounds through speakers — everyone wins

> **Simultaneous output**: SoundBoard now plays through BOTH your speakers (you hear it) AND the CABLE device (Discord friends + OBS viewers hear it).

### For casual use (speakers only):

Just run `SoundBoard.exe` — sounds play through speakers. Mic mode off.

## 🎮 Controls

| Control | Action |
|---------|--------|
| Click button | Play sound |
| `🎲 Random` | Play random weighted sound |
| Volume slider | Global volume |
| Timer switch | Auto-play random sounds |
| `⚙ Settings` | Bind hotkeys, select output device, mic mode |

## 🏗️ Build from Source

```bash
pip install -r requirements.txt
pyinstaller --onefile --windowed --name SoundBoard --hidden-import sounddevice --hidden-import soundfile --hidden-import _soundfile streamer.py
```

## 📋 Requirements

- **Windows 10/11**
- **Python 3.10+** (to build)
- **ffmpeg** (for mic mode, `choco install ffmpeg`)
- **VB-CABLE** (for Discord/OBS mic routing)
- **sounddevice + soundfile** (auto-detected if ffmpeg present)

## 🔊 Audio Routing Diagram

```
SoundBoard ──┬──► Speakers (you hear it)
             │
             └──► CABLE Input ──► CABLE Output ──┬──► Discord mic (friends)
                                                  │
                                                  └──► OBS Audio Capture (viewers)
```

## 📺 OBS Setup (for streamers)

1. In OBS, add **Audio Input Capture** source
2. Select **CABLE Output (VB-Audio Virtual Cable)**
3. In Advanced Audio Properties → set this source to **Monitor Off** (so you don't hear echo)
4. Route to **Stream** only → viewers hear sounds, you don't get doubled audio

## 🔧 VB-CABLE Silent Install (for deployment)

```
VBCABLE_Setup_x64.exe /S
```

## 🎬 Demo

*[Your stream clip here]*

## 📄 License

MIT
