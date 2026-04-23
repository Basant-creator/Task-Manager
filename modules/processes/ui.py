# modules/processes/ui.py
import os
import threading
import time
import getpass
import psutil
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox

REFRESH_INTERVAL = 2.0  # Increased for Windows performance

# THEME A COLORS
BG_MAIN = "#0f0e0f"        # Main background
CARD_BG = "#1a1a1c"        # Outer card
INNER_BG = "#141416"       # Inner table background
TEXT_PRIMARY = "#ffffff"
ROW_ODD = "#121212"
ROW_EVEN = "#151515"
NEON_ACCENT = "#ff8a2b"    # Neon orange strip
NEON_LIME = "#8CFF3E"   # Neon lime for suspend

CORNER = 12


def fmt(x, precision=1):
    try:
        return f"{x:.{precision}f}"
    except:
        return "0.0"


class ProcessesUI(ctk.CTkFrame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, fg_color=BG_MAIN)
        self.parent = parent
        self.current_user = getpass.getuser()
        self._stop = threading.Event()
        self._process_cache = {}
        
        # Track items in trees: {pid: iid}
        self._apps_iids = {}
        self._sys_iids = {}
        
        self._build_ui()
        self._start_background_updates()

    # --------------------------------------------------
    # BUILD INTERFACE
    # --------------------------------------------------
    def _build_ui(self):
        self.pack(fill="both", expand=True)
        padx = 20
        pady = 12

        # Heading
        heading = ctk.CTkLabel(self, text="PROCESSES", 
                               font=ctk.CTkFont(size=26, weight="bold"), 
                               text_color=TEXT_PRIMARY)
        heading.pack(anchor="w", padx=padx, pady=(pady, 0))

        # Top buttons
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=padx, pady=(8, 16))

        self.btn_refresh = ctk.CTkButton(top, text="Refresh", width=120,fg_color="#124c0c", command=self.refresh_now)
        self.btn_kill = ctk.CTkButton(top, text="Kill Selected", width=140, fg_color="#e66b6b", command=self._kill_selected)
        self.btn_suspend = ctk.CTkButton(top, text="Suspend", width=120, fg_color="#ff9b4a", command=self._suspend_selected)

        self.btn_refresh.grid(row=0, column=0, padx=(0,12))
        self.btn_kill.grid(row=0, column=1, padx=(0,12))
        self.btn_suspend.grid(row=0, column=2)

        # Content area
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=padx, pady=(0, pady))

        content.grid_rowconfigure(0, weight=1)
        content.grid_rowconfigure(1, weight=1)
        content.grid_columnconfigure(0, weight=1)

        # Application Processes Card
        self.app_card = self._create_card(content, "Application Processes")
        self.app_card.grid(row=0, column=0, sticky="nsew", pady=(0, 12))

        # System Processes Card
        self.sys_card = self._create_card(content, "System Processes")
        self.sys_card.grid(row=1, column=0, sticky="nsew", pady=(12, 0))

    # --------------------------------------------------
    # CREATE CARD
    # --------------------------------------------------
    def _create_card(self, parent, title):
        outer = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=CORNER)

        # Neon accent strip
        neon = ctk.CTkFrame(outer, width=6, fg_color=NEON_LIME, corner_radius=6)
        neon.place(relx=0, rely=0, relheight=1)

        inner = ctk.CTkFrame(outer, fg_color=INNER_BG, corner_radius=CORNER)
        inner.pack(fill="both", expand=True, padx=(12,14), pady=12)

        lbl = ctk.CTkLabel(inner, text=title, 
                           font=ctk.CTkFont(size=16, weight="bold"), 
                           text_color=TEXT_PRIMARY)
        lbl.pack(anchor="w", padx=12, pady=(0, 10))

        # Table frame
        table_frame = ctk.CTkFrame(inner, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, padx=12, pady=4)

        # Treeview
        columns = ("pid", "name", "cpu", "mem")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="extended")

        tree.heading("pid", text="PID")
        tree.heading("name", text="Name")
        tree.heading("cpu", text="CPU%")
        tree.heading("mem", text="RAM%")

        tree.column("pid", width=100, anchor="w")
        tree.column("name", anchor="w")
        tree.column("cpu", width=90, anchor="center")
        tree.column("mem", width=90, anchor="center")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        tree.pack(side="top", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")

        # Style
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Treeview",
                        background=ROW_ODD,
                        foreground=TEXT_PRIMARY,
                        fieldbackground=ROW_ODD,
                        rowheight=42,
                        font=("Segoe UI", 14))

        style.configure("Treeview.Heading",
                        font=("Segoe UI", 16, "bold"),
                        background=INNER_BG,
                        foreground=TEXT_PRIMARY)

        tree.tag_configure("odd", background=ROW_ODD)
        tree.tag_configure("even", background=ROW_EVEN)

        # Store tree based on title
        if "Application" in title:
            self.apps_tree = tree
        else:
            self.system_tree = tree

        return outer

    # --------------------------------------------------
    # BACKGROUND REFRESH LOOP
    # --------------------------------------------------
    def _start_background_updates(self):
        threading.Thread(target=self._updater_loop, daemon=True).start()

    def _updater_loop(self):
        # Initial CPU call for all processes to prime the counters
        psutil.cpu_percent(interval=None)
        
        while not self._stop.is_set():
            try:
                # Iterate and collect data
                new_cache = {}
                for p in psutil.process_iter(attrs=["pid","name","username","memory_percent"]):
                    try:
                        info = p.info
                        pid = info["pid"]
                        # interval=None is important for non-blocking
                        cpu = p.cpu_percent(interval=None)
                        mem = info["memory_percent"] or 0.0
                        
                        new_cache[pid] = {
                            "pid": pid,
                            "name": info["name"] or "Unknown",
                            "user": info["username"] or "System",
                            "cpu": cpu,
                            "mem": mem
                        }
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                self._process_cache = new_cache
                self.parent.after(0, self._update_ui)

            except Exception:
                pass

            time.sleep(REFRESH_INTERVAL)

    # --------------------------------------------------
    # UI POPULATION (OPTIMIZED SYNC)
    # --------------------------------------------------
    def _update_ui(self):
        apps_data = []
        sys_data = []

        for pid, info in self._process_cache.items():
            user = (info.get("user") or "").lower()
            if user in ("system","nt authority\\system","local service","network service","") or pid == 0:
                sys_data.append(info)
            elif self.current_user.lower() in user:
                apps_data.append(info)
            else:
                sys_data.append(info)

        # Sync trees
        self._sync_tree(self.apps_tree, self._apps_iids, apps_data)
        self._sync_tree(self.system_tree, self._sys_iids, sys_data)

    def _sync_tree(self, tree, iid_map, data):
        new_pids = {it["pid"] for it in data}
        
        # 1. Remove dead
        for pid in list(iid_map.keys()):
            if pid not in new_pids:
                try:
                    tree.delete(iid_map[pid])
                except:
                    pass
                del iid_map[pid]
        
        # 2. Sort
        data = sorted(data, key=lambda x: x["name"].lower())
        
        # 3. Update/Insert
        for i, it in enumerate(data):
            pid = it["pid"]
            vals = (pid, it["name"], fmt(it["cpu"],1), fmt(it["mem"],1))
            tag = "even" if i % 2 == 0 else "odd"
            
            if pid in iid_map:
                try:
                    tree.item(iid_map[pid], values=vals, tags=(tag,))
                except:
                    iid_map[pid] = tree.insert("", "end", values=vals, tags=(tag,))
            else:
                iid_map[pid] = tree.insert("", "end", values=vals, tags=(tag,))

    # --------------------------------------------------
    # BUTTON ACTIONS
    # --------------------------------------------------
    def refresh_now(self):
        # Trigger an immediate cache refresh would be complex with threads,
        # but we can force a UI update from current cache.
        self._update_ui()

    def _get_selected_pids(self):
        pids = []
        for tree in (self.apps_tree, self.system_tree):
            for sel in tree.selection():
                try:
                    item = tree.item(sel)
                    pids.append(int(item["values"][0]))
                except:
                    pass
        return pids

    def _kill_selected(self):
        pids = self._get_selected_pids()
        if not pids: return
        if messagebox.askyesno("Confirm", f"Kill {len(pids)} selected process(es)?"):
            for pid in pids:
                try:
                    psutil.Process(pid).kill()
                except Exception as e:
                    messagebox.showerror("Error", f"PID {pid}: {e}")

    def _suspend_selected(self):
        pids = self._get_selected_pids()
        for pid in pids:
            try:
                psutil.Process(pid).suspend()
            except Exception as e:
                messagebox.showerror("Error", f"PID {pid}: {e}")

    def destroy(self):
        self._stop.set()
        super().destroy()
