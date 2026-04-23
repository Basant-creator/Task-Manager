# modules/performance/ui.py
import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import time
from modules import styles
from modules.performance import backend as perf_backend
import collections

UPDATE_INTERVAL = 1.0  # Increase to 1.0s for better performance on Windows

class PerformanceUI:
    def __init__(self, parent):
        self.parent = parent
        self.running = True

        self.prev_net = {"sent": 0, "recv": 0}

        # fixed length buffers (60 samples)
        self.maxlen = 60  # 60 samples at 1.0s = 1 minute of history
        self.cpu_hist = collections.deque([0.0]*self.maxlen, maxlen=self.maxlen)
        self.ram_hist = collections.deque([0.0]*self.maxlen, maxlen=self.maxlen)
        self.disk_hist = collections.deque([0.0]*self.maxlen, maxlen=self.maxlen)
        self.gpu_hist = collections.deque([0.0]*self.maxlen, maxlen=self.maxlen)
        self.gpu_mem_hist = collections.deque([0.0]*self.maxlen, maxlen=self.maxlen)
        self.net_down_hist = collections.deque([0.0]*self.maxlen, maxlen=self.maxlen)
        self.net_up_hist = collections.deque([0.0]*self.maxlen, maxlen=self.maxlen)

        self._build_ui()
        # start background updater
        self.updater_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.updater_thread.start()

    def _build_ui(self):
        self.parent.configure(fg_color=styles.BG_MAIN)

        # Title
        header = ctk.CTkFrame(self.parent, fg_color=styles.BG_MAIN)
        header.pack(fill="x", padx=16, pady=(12,6))
        ctk.CTkLabel(header, text="PERFORMANCE", font=ctk.CTkFont(size=26, weight="bold"),
                     text_color=styles.TEXT_PRIMARY).pack(side="left")
        ctk.CTkLabel(header, text="System Resource Monitoring", font=ctk.CTkFont(size=12),
                     text_color=styles.NEON_ORANGE).pack(side="left", padx=10)

        # Top metric cards (CPU, RAM, DISK, NET)
        top = ctk.CTkFrame(self.parent, fg_color=styles.BG_MAIN)
        top.pack(fill="x", padx=16, pady=(6,8))

        self.val_cpu = self._create_value_card(top, "CPU", styles.NEON_ORANGE)
        self.val_ram = self._create_value_card(top, "RAM", styles.NEON_BLUE)
        self.val_disk = self._create_value_card(top, "DISK", styles.NEON_YELLOW)
        self.val_net = self._create_value_card(top, "NET", styles.NEON_CYAN)

        # Graph grid
        grid = ctk.CTkFrame(self.parent, fg_color=styles.BG_MAIN)
        grid.pack(fill="both", expand=True, padx=16, pady=(6,16))
        grid.grid_columnconfigure((0,1), weight=1)
        grid.grid_rowconfigure((0,1,2,3), weight=1)

        self.card_disk = self._create_graph_card(grid, "Disk Usage", 0, 0, styles.NEON_YELLOW)
        self.card_ram = self._create_graph_card(grid, "Memory Usage", 0, 1, styles.NEON_BLUE)
        self.card_gpu_mem = self._create_graph_card(grid, "GPU Memory", 1, 0, styles.NEON_PINK)
        self.card_gpu_usage = self._create_graph_card(grid, "GPU Usage", 1, 1, styles.NEON_PURPLE)
        self.card_cpu = self._create_graph_card(grid, "CPU Usage", 2, 0, styles.NEON_ORANGE, colspan=2)
        self.card_net = self._create_graph_card(grid, "Network I/O", 3, 0, styles.NEON_CYAN, colspan=2, multi=True)

    def _create_value_card(self, parent, title, accent):
        frame = ctk.CTkFrame(parent, fg_color=styles.CARD_BG, corner_radius=styles.CORNER_RADIUS)
        frame.pack(side="left", expand=True, fill="both", padx=8, pady=4)

        lbl = ctk.CTkLabel(frame, text=title, text_color=styles.TEXT_PRIMARY, font=ctk.CTkFont(size=14, weight="bold"))
        lbl.pack(anchor="w", padx=12, pady=(8,0))
        val = ctk.CTkLabel(frame, text="0.0%", text_color=accent, font=ctk.CTkFont(size=20, weight="bold"))
        val.pack(anchor="w", padx=12, pady=(4,12))
        return val

    def _create_graph_card(self, parent, title, r, c, color, colspan=1, multi=False):
        card = ctk.CTkFrame(parent, fg_color=styles.CARD_BG, corner_radius=styles.CORNER_RADIUS)
        card.grid(row=r, column=c, columnspan=colspan, sticky="nsew", padx=8, pady=8)
        # title
        t = ctk.CTkLabel(card, text=title, text_color=styles.TEXT_PRIMARY,
                         font=ctk.CTkFont(size=16, weight="bold"))
        t.pack(anchor="w", padx=10, pady=(10,4))

        fig = plt.Figure(figsize=(6,2.4), dpi=80) # Lower DPI for better performance
        ax = fig.add_subplot(111)
        ax.set_facecolor(styles.CARD_BG)
        fig.patch.set_facecolor(styles.CARD_BG)
        ax.tick_params(colors="white", labelsize=8)
        for spine in ax.spines.values():
            spine.set_color("#222225")
        
        ax.set_ylim(0, 100) # Pre-set Y limit for most charts
        x = range(self.maxlen)
        initial_data = [0]*self.maxlen

        if multi:
            # network has two lines
            line_down, = ax.plot(x, initial_data, color=styles.NEON_CYAN, linewidth=styles.GRAPH_LINEWIDTH)
            line_up, = ax.plot(x, initial_data, color=styles.NEON_LIME, linewidth=styles.GRAPH_LINEWIDTH)
            ax.legend(["Down KB/s", "Up KB/s"], facecolor=styles.CARD_BG, labelcolor=styles.TEXT_PRIMARY, fontsize=8)
            ax.set_ylim(auto=True) # Network needs auto-scale
            fill_down = None
            fill_up = None
        else:
            line, = ax.plot(x, initial_data, color=color, linewidth=styles.GRAPH_LINEWIDTH)
            line_down = line_up = None
            fill_down = None
            fill_up = None

        canvas = FigureCanvasTkAgg(fig, master=card)
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(6,10))

        return {"card": card, "ax": ax, "fig": fig, "canvas": canvas, "color": color,
                "line": line if not multi else None, "line_down": line_down, "line_up": line_up, 
                "fill_down": fill_down, "multi": multi}

    # -------- update loop in background thread (collect samples)
    def _update_loop(self):
        while self.running:
            try:
                cpu = perf_backend.get_cpu_percent()
                ram = perf_backend.get_ram_percent()
                disk = perf_backend.get_disk_percent()
                down, up = perf_backend.get_network_delta(self.prev_net)
                gpu, gpu_mem = perf_backend.get_gpu_metrics_placeholder()

                # append
                self.cpu_hist.append(cpu)
                self.ram_hist.append(ram)
                self.disk_hist.append(disk)
                self.gpu_hist.append(gpu)
                self.gpu_mem_hist.append(gpu_mem)
                self.net_down_hist.append(down)
                self.net_up_hist.append(up)

                # schedule UI update on main thread
                self.parent.after(0, self._refresh_ui)
            except Exception:
                pass

            time.sleep(UPDATE_INTERVAL)

    def _refresh_ui(self):
        if not self.running: return
        # update numeric cards
        if self.cpu_hist:
            self.val_cpu.configure(text=f"{self.cpu_hist[-1]:.1f}%")
        if self.ram_hist:
            self.val_ram.configure(text=f"{self.ram_hist[-1]:.1f}%")
        if self.disk_hist:
            self.val_disk.configure(text=f"{self.disk_hist[-1]:.1f}%")
        if self.net_down_hist:
            self.val_net.configure(text=f"{self.net_down_hist[-1]:.1f} KB/s")

        # update graphs efficiently
        self._update_graph(self.card_cpu, self.cpu_hist)
        self._update_graph(self.card_ram, self.ram_hist)
        self._update_graph(self.card_disk, self.disk_hist)
        self._update_graph(self.card_gpu_usage, self.gpu_hist)
        self._update_graph(self.card_gpu_mem, self.gpu_mem_hist)
        self._update_network_graph(self.card_net, self.net_down_hist, self.net_up_hist)

    def _update_graph(self, card, data):
        line = card["line"]
        line.set_ydata(list(data))
        # We skip fill_between for pure performance on Windows, 
        # or we could redraw it less often. For now, just the line.
        card["canvas"].draw_idle()

    def _update_network_graph(self, card, down, up):
        card["line_down"].set_ydata(list(down))
        card["line_up"].set_ydata(list(up))
        card["ax"].relim()
        card["ax"].autoscale_view()
        card["canvas"].draw_idle()

    def stop_updates(self):
        self.running = False


    def stop_updates(self):
        self.running = False
