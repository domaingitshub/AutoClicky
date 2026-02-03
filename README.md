# AutoClicky

A simple hotkey-driven autoclicker written in Python. Use it for repetitive clicking tasks with adjustable interval, jitter, and duration.

## Features
- Start/pause toggling with a hotkey
- Stop-and-exit hotkey
- Adjustable interval and optional random jitter
- Optional auto-stop duration

## Requirements
- Python 3.10+
- [`pynput`](https://pypi.org/project/pynput/)

## Install
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run
```bash
python src/autoclicker.py --interval 0.2 --jitter 0.05
```

### Default hotkeys
- Toggle start/pause: `Ctrl+Alt+T`
- Stop and exit: `Ctrl+Alt+S`

Override them if needed:
```bash
python src/autoclicker.py --toggle-hotkey "<ctrl>+<shift>+t" --stop-hotkey "<esc>"
```

## Notes
- Some OSes require accessibility permissions for keyboard/mouse control.
- Use responsibly and comply with the terms of any application you automate.
