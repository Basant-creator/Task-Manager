# modules/performance/backend.py
import psutil
import platform
import time

def get_cpu_percent():
    return psutil.cpu_percent(interval=None)

def get_ram_percent():
    return psutil.virtual_memory().percent

def get_disk_percent(path="/"):
    try:
        return psutil.disk_usage(path).percent
    except Exception:
        return 0.0

def get_network_delta(prev):
    io = psutil.net_io_counters()
    sent = io.bytes_sent
    recv = io.bytes_recv
    down_kb = max(0.0, (recv - prev.get("recv", recv)) / 1024.0)
    up_kb = max(0.0, (sent - prev.get("sent", sent)) / 1024.0)
    prev["recv"] = recv
    prev["sent"] = sent
    return down_kb, up_kb

def get_gpu_metrics_placeholder():
    # GPU not available: return zeros
    return 0.0, 0.0
