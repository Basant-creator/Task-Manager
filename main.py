# main.py
import os
import sys
import customtkinter as ctk

# ensure project root in path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from modules import styles
from modules.performance.ui import PerformanceUI
from modules.processes.ui import ProcessesUI
from modules.startup.ui import StartupUI
from modules.settings.ui import SettingsUI  # lightweight placeholder

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("System Monitoring Dashboard")
        self.root.geometry("1400x820")
        self.root.minsize(1100, 700)

        self.current_page = None
        self.pages = {}

        self._create_sidebar()
        self._create_content_area()
        self.show_performance()

    def _create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self.root, fg_color=styles.SIDEBAR_BG, width=220, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Title
        title_frame = ctk.CTkFrame(self.sidebar, fg_color=styles.SIDEBAR_BG)
        title_frame.pack(fill="x", padx=18, pady=(18, 8))
        ctk.CTkLabel(title_frame, text="DASHBOARD", font=ctk.CTkFont(size=26, weight="bold"),
                     text_color=styles.TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(title_frame, text="System Monitor", font=ctk.CTkFont(size=11),
                     text_color=styles.NEON_ORANGE).pack(anchor="w", pady=(2, 4))

        btn_kwargs = dict(width=180, height=44, corner_radius=10)
        self.btn_perf = ctk.CTkButton(self.sidebar, text="Performance", command=self.show_performance,
                                      fg_color=styles.NEON_ORANGE, text_color=styles.TEXT_PRIMARY,
                                      font=ctk.CTkFont(size=14, weight="bold"), **btn_kwargs)
        self.btn_perf.pack(padx=18, pady=(6, 8))

        self.btn_proc = ctk.CTkButton(self.sidebar, text="Processes", command=self.show_processes,
                                      fg_color=styles.SIDEBAR_BG, hover_color=styles.CARD_BG_ALT,
                                      text_color=styles.TEXT_PRIMARY, font=ctk.CTkFont(size=14, weight="bold"),
                                      **btn_kwargs)
        self.btn_proc.pack(padx=18, pady=6)

        self.btn_startup = ctk.CTkButton(self.sidebar, text="Startup Apps", command=self.show_startup,
                                         fg_color=styles.SIDEBAR_BG, hover_color=styles.CARD_BG_ALT,
                                         text_color=styles.TEXT_PRIMARY, font=ctk.CTkFont(size=14, weight="bold"),
                                         **btn_kwargs)
        self.btn_startup.pack(padx=18, pady=6)

        self.btn_settings = ctk.CTkButton(self.sidebar, text="Settings", command=self.show_settings,
                                          fg_color=styles.SIDEBAR_BG, hover_color=styles.CARD_BG_ALT,
                                          text_color=styles.TEXT_PRIMARY, font=ctk.CTkFont(size=14, weight="bold"),
                                          **btn_kwargs)
        self.btn_settings.pack(padx=18, pady=6)

        ctk.CTkLabel(self.sidebar, text="v1.0 • MONITORING ACTIVE", text_color=styles.TEXT_MUTED,
                     font=ctk.CTkFont(size=9)).pack(side="bottom", pady=12)

    def _create_content_area(self):
        self.content = ctk.CTkFrame(self.root, fg_color=styles.BG_MAIN)
        self.content.pack(side="right", fill="both", expand=True)

    def _clear_content(self):
        # stop page updates if exists
        try:
            if self.current_page and hasattr(self.pages[self.current_page], "stop_updates"):
                self.pages[self.current_page].stop_updates()
        except Exception:
            pass
        for w in self.content.winfo_children():
            w.destroy()

    def _highlight_button(self, active_btn):
        for b in (self.btn_perf, self.btn_proc, self.btn_startup, self.btn_settings):
            b.configure(fg_color=styles.SIDEBAR_BG)
        active_btn.configure(fg_color=styles.NEON_ORANGE)

    def show_performance(self):
        self._clear_content()
        self._highlight_button(self.btn_perf)
        page = PerformanceUI(self.content)
        self.pages["performance"] = page
        self.current_page = "performance"

    def show_processes(self):
        self._clear_content()
        self._highlight_button(self.btn_proc)
        page = ProcessesUI(self.content)
        self.pages["processes"] = page
        self.current_page = "processes"

    def show_startup(self):
        self._clear_content()
        self._highlight_button(self.btn_startup)
        page = StartupUI(self.content)
        self.pages["startup"] = page
        self.current_page = "startup"

    def show_settings(self):
        self._clear_content()
        self._highlight_button(self.btn_settings)
        page = SettingsUI(self.content)
        self.pages["settings"] = page
        self.current_page = "settings"


if __name__ == "__main__":
    root = ctk.CTk()
    app = MainApp(root)
    root.mainloop()
