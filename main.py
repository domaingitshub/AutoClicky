import random
import threading
import time
from dataclasses import dataclass

import ttkbootstrap as ttk
from pynput import keyboard, mouse


@dataclass
class ClickerConfig:
    interval_ms: int
    button: mouse.Button
    humanize: bool
    jitter_pct: float


class AutoClickerApp:
    def __init__(self) -> None:
        self.style = ttk.Style(theme="flatly")
        self.root = self.style.master
        self.root.title("AutoClicky")
        self.root.geometry("520x420")
        self.root.resizable(False, False)

        self.mouse_controller = mouse.Controller()
        self.click_thread: threading.Thread | None = None
        self.stop_event = threading.Event()
        self.is_running = False

        self.interval_var = ttk.StringVar(value="100")
        self.button_var = ttk.StringVar(value="left")
        self.humanize_var = ttk.BooleanVar(value=True)
        self.status_var = ttk.StringVar(value="Ready")
        self.clicks_var = ttk.StringVar(value="0")
        self.cps_var = ttk.StringVar(value="10.00")
        self.hotkey_var = ttk.StringVar(value="F6")

        self._build_ui()
        self._bind_events()
        self._start_hotkey_listener()

    def _build_ui(self) -> None:
        container = ttk.Frame(self.root, padding=18)
        container.pack(fill="both", expand=True)

        header = ttk.Frame(container)
        header.pack(fill="x")
        ttk.Label(
            header,
            text="AutoClicky",
            font=("Segoe UI", 20, "bold"),
        ).pack(anchor="w")
        ttk.Label(
            header,
            text="Beautiful, reliable auto-clicking for daily workflows.",
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(4, 12))

        settings = ttk.LabelFrame(container, text="Click Settings", padding=12)
        settings.pack(fill="x")

        ttk.Label(settings, text="Interval (ms)").grid(row=0, column=0, sticky="w")
        interval_entry = ttk.Entry(settings, textvariable=self.interval_var, width=12)
        interval_entry.grid(row=0, column=1, sticky="w", padx=(8, 16))

        ttk.Label(settings, text="Clicks/sec").grid(row=0, column=2, sticky="w")
        ttk.Label(settings, textvariable=self.cps_var).grid(row=0, column=3, sticky="w")

        ttk.Label(settings, text="Mouse button").grid(row=1, column=0, sticky="w", pady=(10, 0))
        ttk.Combobox(
            settings,
            textvariable=self.button_var,
            values=("left", "right"),
            width=10,
            state="readonly",
        ).grid(row=1, column=1, sticky="w", padx=(8, 16), pady=(10, 0))

        ttk.Checkbutton(
            settings,
            text="Humanize timing (adds slight jitter for natural clicks)",
            variable=self.humanize_var,
        ).grid(row=2, column=0, columnspan=4, sticky="w", pady=(10, 0))

        status_frame = ttk.LabelFrame(container, text="Status", padding=12)
        status_frame.pack(fill="x", pady=(14, 0))
        ttk.Label(status_frame, text="Status").grid(row=0, column=0, sticky="w")
        ttk.Label(status_frame, textvariable=self.status_var, font=("Segoe UI", 10, "bold")).grid(
            row=0, column=1, sticky="w", padx=(8, 16)
        )
        ttk.Label(status_frame, text="Total clicks").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Label(status_frame, textvariable=self.clicks_var).grid(
            row=1, column=1, sticky="w", padx=(8, 16), pady=(8, 0)
        )
        ttk.Label(status_frame, text="Hotkey").grid(row=0, column=2, sticky="w")
        ttk.Label(status_frame, textvariable=self.hotkey_var).grid(row=0, column=3, sticky="w")

        controls = ttk.Frame(container)
        controls.pack(fill="x", pady=(16, 0))
        self.start_button = ttk.Button(
            controls,
            text="Start Clicking",
            style="success.TButton",
            command=self.toggle_clicking,
            width=20,
        )
        self.start_button.pack(side="left")
        ttk.Button(
            controls,
            text="Reset Count",
            style="secondary.TButton",
            command=self.reset_count,
            width=16,
        ).pack(side="left", padx=(10, 0))

        tips = ttk.Frame(container)
        tips.pack(fill="x", pady=(16, 0))
        ttk.Label(
            tips,
            text="Tip: Press F6 anytime to start/stop. Keep the app running for hotkey access.",
            font=("Segoe UI", 9),
            foreground="#667085",
        ).pack(anchor="w")

    def _bind_events(self) -> None:
        self.interval_var.trace_add("write", lambda *_: self._update_cps())
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _start_hotkey_listener(self) -> None:
        def on_press(key: keyboard.Key | keyboard.KeyCode) -> None:
            if key == keyboard.Key.f6:
                self.root.after(0, self.toggle_clicking)

        listener = keyboard.Listener(on_press=on_press)
        listener.daemon = True
        listener.start()

    def _update_cps(self) -> None:
        interval_ms = self._parse_interval()
        cps = 1000 / interval_ms if interval_ms > 0 else 0
        self.cps_var.set(f"{cps:.2f}")

    def _parse_interval(self) -> int:
        try:
            interval_ms = int(self.interval_var.get().strip())
        except ValueError:
            interval_ms = 0
        return max(interval_ms, 0)

    def _build_config(self) -> ClickerConfig | None:
        interval_ms = self._parse_interval()
        if interval_ms <= 0:
            self.status_var.set("Enter a valid interval (ms).")
            return None
        button_value = self.button_var.get()
        button = mouse.Button.left if button_value == "left" else mouse.Button.right
        return ClickerConfig(
            interval_ms=interval_ms,
            button=button,
            humanize=self.humanize_var.get(),
            jitter_pct=0.15,
        )

    def toggle_clicking(self) -> None:
        if self.is_running:
            self.stop_clicking()
        else:
            self.start_clicking()

    def start_clicking(self) -> None:
        config = self._build_config()
        if not config:
            return

        self.stop_event.clear()
        self.is_running = True
        self.status_var.set("Running")
        self.start_button.config(text="Stop Clicking", style="danger.TButton")
        self.click_thread = threading.Thread(
            target=self._click_loop,
            args=(config,),
            daemon=True,
        )
        self.click_thread.start()

    def stop_clicking(self) -> None:
        self.stop_event.set()
        self.is_running = False
        self.status_var.set("Paused")
        self.start_button.config(text="Start Clicking", style="success.TButton")

    def reset_count(self) -> None:
        self.clicks_var.set("0")

    def _click_loop(self, config: ClickerConfig) -> None:
        interval_s = config.interval_ms / 1000
        next_time = time.perf_counter()
        while not self.stop_event.is_set():
            jitter = 1.0
            if config.humanize:
                jitter = random.uniform(1 - config.jitter_pct, 1 + config.jitter_pct)
            effective_interval = interval_s * jitter
            next_time += effective_interval
            self.mouse_controller.click(config.button)
            self.root.after(0, self._increment_clicks)
            sleep_for = max(0, next_time - time.perf_counter())
            time.sleep(sleep_for)

    def _increment_clicks(self) -> None:
        current = int(self.clicks_var.get())
        self.clicks_var.set(str(current + 1))

    def _on_close(self) -> None:
        self.stop_clicking()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    AutoClickerApp().run()
