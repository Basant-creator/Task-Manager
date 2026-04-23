# modules/startup/ui.py
import os
import platform
import threading
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox

IS_WINDOWS = platform.system() == "Windows"
if IS_WINDOWS:
    import winreg

# THEME A COLORS
BG_MAIN = "#0f0e0f"
CARD_BG = "#1a1a1c"
INNER_BG = "#141416"
TEXT_PRIMARY = "#FFFFFF"
ROW_ODD = "#121212"
ROW_EVEN = "#151515"
NEON_ACCENT = "#ff8a2b"
NEON_CYAN = "#00FFD6" 
GLOW = "#146B84" 

CORNER = 12


class StartupUI(ctk.CTkFrame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, fg_color=BG_MAIN)
        self.parent = parent
        self.pack(fill="both", expand=True)
        self._build_ui()

        if IS_WINDOWS:
            self.load_entries()
        else:
            self.tree.insert("", "end", values=("Not supported", "", "", ""))

    # --------------------------------------------------
    # BUILD UI
    # --------------------------------------------------
    def _build_ui(self):
        padx = 20
        pady = 12

        # Heading
        heading = ctk.CTkLabel(self, text="STARTUP APPS",
                               font=ctk.CTkFont(size=26, weight="bold"),
                               text_color=TEXT_PRIMARY)
        heading.pack(anchor="w", padx=padx, pady=(pady, 4))

        # Buttons row
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=padx, pady=(4, 16))

        self.btn_refresh = ctk.CTkButton(top, text="Refresh", width=125, command=self.load_entries)
        self.btn_enable = ctk.CTkButton(top, text="Enable", width=125, fg_color="#00d29c")
        self.btn_disable = ctk.CTkButton(top, text="Disable", width=125, fg_color="#e66b6b")
        self.btn_open = ctk.CTkButton(top, text="Open Location", width=150, fg_color=NEON_ACCENT)

        self.btn_refresh.grid(row=0, column=0, padx=(0,12))
        self.btn_enable.grid(row=0, column=1, padx=(0,12))
        self.btn_disable.grid(row=0, column=2, padx=(0,12))
        self.btn_open.grid(row=0, column=3)

        # Content card
        outer = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=CORNER)
        outer.pack(fill="both", expand=True, padx=padx, pady=(0, pady))

        # Neon strip
        neon = ctk.CTkFrame(outer, width=6, fg_color=NEON_CYAN, corner_radius=6)
        neon.place(relx=0, rely=0, relheight=1)

        inner = ctk.CTkFrame(outer, fg_color=INNER_BG, corner_radius=CORNER)
        inner.pack(fill="both", expand=True, padx=(12,14), pady=16)

        # Table container
        table = ctk.CTkFrame(inner, fg_color="transparent")
        table.pack(fill="both", expand=True, padx=12, pady=8)

        cols = ("name", "command", "location", "enabled")
        self.tree = ttk.Treeview(table, columns=cols, show="headings")

        # Headings
        self.tree.heading("name", text="Name")
        self.tree.heading("command", text="Command")
        self.tree.heading("location", text="Location")
        self.tree.heading("enabled", text="Enabled")

        # Columns width
        self.tree.column("name", width=220, anchor="w")
        self.tree.column("command", width=650, anchor="w")
        self.tree.column("location", width=250, anchor="w")
        self.tree.column("enabled", width=80, anchor="center")

        # Scrollbars
        vsb = ttk.Scrollbar(table, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")

        # Treeview style
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Treeview",
                        background=ROW_ODD,
                        foreground=TEXT_PRIMARY,
                        fieldbackground=ROW_ODD,
                        rowheight=62,
                        font=("Segoe UI", 14))

        style.configure("Treeview.Heading",
                        font=("Segoe UI", 16, "bold"),
                        background=INNER_BG,
                        # background=GLOW,
                        foreground=TEXT_PRIMARY)

        self.tree.tag_configure("odd", background=ROW_ODD)
        self.tree.tag_configure("even", background=ROW_EVEN)

    # --------------------------------------------------
    # LOAD ENTRIES
    # --------------------------------------------------
    def load_entries(self):
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        if not IS_WINDOWS:
            return

        # Clear table
        for i in self.tree.get_children():
            self.tree.delete(i)

        run_keys = [
            (winreg.HKEY_CURRENT_USER,  r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run")
        ]

        entries = []
        seen = set()

        for root, path in run_keys:
            try:
                with winreg.OpenKey(root, path) as k:
                    i = 0
                    while True:
                        try:
                            name, value, _ = winreg.EnumValue(k, i)
                            if name not in seen:
                                seen.add(name)
                                loc = "HKCU" if root == winreg.HKEY_CURRENT_USER else "HKLM"
                                entries.append((name, value, f"{loc}:{path}", "Yes"))
                            i += 1
                        except OSError:
                            break
            except:
                continue

        # Sort by name
        entries.sort(key=lambda x: x[0].lower())

        # Insert into table
        for idx, e in enumerate(entries):
            tag = "even" if idx % 2 == 0 else "odd"
            self.tree.insert("", "end", values=e, tags=(tag,))

    # --------------------------------------------------
    # BUTTON ACTIONS
    # --------------------------------------------------
    def _get_selected(self):
        sel = self.tree.selection()
        if not sel:
            return None
        return self.tree.item(sel[0])["values"]

    def _open_location_selected(self):
        row = self._get_selected()
        if not row:
            return

        cmd = row[1]
        if '"' in cmd:
            try:
                path = cmd.split('"')[1]
            except:
                path = cmd
        else:
            path = cmd.split(" ")[0]

        if os.path.exists(path):
            os.startfile(os.path.dirname(path))
        else:
            messagebox.showwarning("Not Found", f"Cannot open:\n{path}")

    def _enable_selected(self):
        messagebox.showinfo("Info", "Enable requires registry write. I can add this safely if you want.")

    def _disable_selected(self):
        messagebox.showinfo("Info", "Disable requires registry write. I can add this safely if you want.")
