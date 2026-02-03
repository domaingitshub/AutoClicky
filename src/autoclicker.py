#!/usr/bin/env python3
"""Simple, hotkey-driven autoclicker."""

from __future__ import annotations

import argparse
import random
import threading
import time
from dataclasses import dataclass
from typing import Callable

from pynput import keyboard, mouse


@dataclass
class ClickConfig:
    interval: float
    jitter: float
    button: mouse.Button
    duration: float | None


class AutoClicker:
    def __init__(self, config: ClickConfig) -> None:
        self.config = config
        self._mouse = mouse.Controller()
        self._active = threading.Event()
        self._stop = threading.Event()
        self._worker = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self._worker.start()

    def toggle(self) -> None:
        if self._active.is_set():
            self._active.clear()
            print("Paused clicking.")
        else:
            self._active.set()
            print("Started clicking.")

    def stop(self) -> None:
        self._stop.set()
        self._active.set()

    def _run(self) -> None:
        start_time = None
        while not self._stop.is_set():
            if not self._active.is_set():
                time.sleep(0.05)
                continue
            if start_time is None:
                start_time = time.time()
            if self.config.duration is not None:
                elapsed = time.time() - start_time
                if elapsed >= self.config.duration:
                    print("Duration reached. Stopping.")
                    self.stop()
                    break
            self._mouse.click(self.config.button)
            delay = self.config.interval
            if self.config.jitter:
                delay = max(0.01, delay + random.uniform(-self.config.jitter, self.config.jitter))
            time.sleep(delay)


def parse_button(name: str) -> mouse.Button:
    mapping = {
        "left": mouse.Button.left,
        "right": mouse.Button.right,
        "middle": mouse.Button.middle,
    }
    try:
        return mapping[name]
    except KeyError as exc:
        raise argparse.ArgumentTypeError(f"Unsupported button: {name}") from exc


def build_hotkey(hotkey_str: str, callback: Callable[[], None]) -> keyboard.HotKey:
    return keyboard.HotKey(keyboard.HotKey.parse(hotkey_str), callback)


def main() -> None:
    parser = argparse.ArgumentParser(description="Hotkey-controlled autoclicker.")
    parser.add_argument("--interval", type=float, default=0.2, help="Seconds between clicks.")
    parser.add_argument("--jitter", type=float, default=0.0, help="Random +/- jitter in seconds.")
    parser.add_argument("--button", type=parse_button, default="left", help="left/right/middle")
    parser.add_argument("--duration", type=float, default=None, help="Auto-stop after N seconds.")
    parser.add_argument("--toggle-hotkey", default="<ctrl>+<alt>+t", help="Hotkey to start/pause.")
    parser.add_argument("--stop-hotkey", default="<ctrl>+<alt>+s", help="Hotkey to stop and exit.")
    args = parser.parse_args()

    config = ClickConfig(
        interval=max(0.01, args.interval),
        jitter=max(0.0, args.jitter),
        button=args.button,
        duration=args.duration,
    )
    clicker = AutoClicker(config)
    clicker.start()

    toggle_hotkey = build_hotkey(args.toggle_hotkey, clicker.toggle)
    stop_hotkey = build_hotkey(args.stop_hotkey, clicker.stop)

    def for_canonical(handler: Callable[[keyboard.KeyCode], None]) -> Callable[[keyboard.KeyCode], None]:
        return lambda key: handler(listener.canonical(key))

    listener = keyboard.Listener(
        on_press=for_canonical(lambda key: (toggle_hotkey.press(key), stop_hotkey.press(key))),
        on_release=for_canonical(lambda key: (toggle_hotkey.release(key), stop_hotkey.release(key))),
    )
    listener.start()

    print("Autoclicker ready.")
    print(f"Toggle: {args.toggle_hotkey} | Stop: {args.stop_hotkey}")

    try:
        while not clicker._stop.is_set():
            time.sleep(0.1)
    except KeyboardInterrupt:
        clicker.stop()
    finally:
        listener.stop()


if __name__ == "__main__":
    main()
