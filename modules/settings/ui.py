# modules/settings/ui.py
import customtkinter as ctk
from modules import styles

class SettingsUI:
    def __init__(self, parent):
        self.parent = parent
        self.parent.configure(fg_color=styles.BG_MAIN)
        self.build()

    def build(self):
        frame = ctk.CTkFrame(self.parent, fg_color=styles.BG_MAIN)
        frame.pack(fill="both", expand=True, padx=16, pady=16)
        ctk.CTkLabel(frame, text="SETTINGS", text_color=styles.TEXT_PRIMARY, font=ctk.CTkFont(size=26, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(frame, text="(Add settings later)", text_color=styles.TEXT_MUTED).pack(anchor="w", pady=(6,0))
