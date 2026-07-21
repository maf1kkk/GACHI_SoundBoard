# SoundBoard — Streamer Soundboard with Discord Mic Support

A desktop soundboard app for streamers with weighted random selection, hotkey bindings, and optional microphone output via virtual audio cable (VB-CABLE).

![SoundBoard Screenshot](screenshot.png)

## Features

- **344+ GachiMuchi sounds** — weighted random picks short/funny sounds 3x more often
- **Discord/Voice chat support** — route sounds through VB-CABLE to your mic (like Soundpad)
- **Hotkey bindings** — bind any key to any sound, works in background
- **Random timer** — plays random sounds at configurable intervals
- **Per-sound volume** — global volume slider
- **Dark theme** — customtkinter modern UI

## How to Use

1. **Download** the latest `SoundBoard.exe` from Releases
2. **Place sounds** in a `sounds/` folder next to the exe (MP3, WAV, OGG, FLAC, M4A)
3. **Run** `SoundBoard.exe`
4. Click a sound button or press a hotkey
5. For **Discord mic mode**, install [VB-CABLE](https://vb-audio.com/Cable/), select `CABLE Input` as output device, enable "Play through microphone", and set `CABLE Output` as your Discord input device

## Build from Source

```bash
pip install -r requirements.txt
pyinstaller --onefile --windowed --name SoundBoard --hidden-import sounddevice --hidden-import soundfile --hidden-import _soundfile streamer.py
```

## Requirements

- Windows 10/11
- Python 3.10+ (to build)
- ffmpeg (for mic mode, optional)

## License

MIT
