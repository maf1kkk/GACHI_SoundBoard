# GACHI SoundBoard

Desktop soundboard for streamers with weighted random sound selection, hotkey bindings, timer, and audio routing to Discord/OBS via virtual audio cable.

## Features

- 300+ GachiMuchi sounds with weighted random selection (short/funny sounds 3x more likely)
- Audio routing to Discord microphone via VB-CABLE virtual audio driver
- Capture as separate audio source in OBS (Audio Input Capture -> CABLE Output)
- Hotkey bindings for each sound, works in background
- Random timer with configurable interval
- Mic gain control (50-500%) for volume adjustment
- Simultaneous output to speakers + Discord mic
- Dark theme UI

## Quick Start

### For streaming (Discord + OBS)

1. Install [VB-CABLE](https://vb-audio.com/Cable/) (free virtual audio driver, requires reboot)
2. Download `SoundBoard.exe` and place it next to a `sounds/` folder with MP3/WAV files
3. In SoundBoard -> Settings -> select `CABLE Input` as output device -> enable "Play through microphone"
4. Set Mic Gain to 200-300% if sound is too quiet
5. In Discord -> Voice & Video -> Input Device -> `CABLE Output`
6. In OBS -> add Audio Input Capture -> `CABLE Output` -> route to Stream only

Sound now plays simultaneously through your speakers and the virtual cable. You hear it, Discord friends hear it, OBS viewers hear it as a separate audio track.

### For casual use

Run `SoundBoard.exe` with mic mode disabled. Sounds play through speakers only.

## Controls

| Control | Action |
|---------|--------|
| Sound button | Play sound |
| Random button | Play random weighted sound |
| Volume slider | Global playback volume |
| Timer switch | Enable/disable auto-play |
| Settings button | Hotkey bindings, output device, mic mode, gain |

## Audio Routing

```
SoundBoard --+--> Speakers (local)
             |
             +--> CABLE Input -> CABLE Output --+--> Discord (friends)
                                                |
                                                +--> OBS (viewers)
```

## Build from Source

```bash
pip install -r requirements.txt
pyinstaller --onefile --windowed --name SoundBoard --hidden-import sounddevice --hidden-import soundfile --hidden-import _soundfile streamer.py
```

## Requirements

- Windows 10/11
- Python 3.10+ (to build)
- ffmpeg (for mic mode, `choco install ffmpeg`)
- VB-CABLE (for Discord/OBS audio routing)
- sounddevice + soundfile (auto-detected if ffmpeg present)

## Demo

<video src="https://github.com/maf1kkk/GACHI_SoundBoard/raw/master/%D0%92%D0%B8%D0%B4%D0%B5%D0%BE%20%D1%81%D0%BE%20%D1%81%D1%82%D1%80%D0%B8%D0%BC%D0%B0/%D0%9F%D1%80%D0%B8%D0%BC%D0%B5%D1%80%20%D1%80%D0%B0%D0%B1%D0%BE%D1%82%D1%8B%20%D0%A1%D0%B0%D1%83%D0%BD%D0%B4%D0%91%D0%BE%D0%B0%D1%80%D0%B4%D0%B0%20%D1%81%D0%BE%20%D1%81%D1%82%D1%80%D0%B8%D0%BC%D0%B0.mp4" controls width="100%"></video>

## License

MIT
