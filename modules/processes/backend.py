# modules/processes/backend.py
import psutil
import threading
from modules.utils.cache import global_cache

# Prime CPU counters
psutil.cpu_percent(interval=None)

def fetch_all_processes():
    cache_key = "processes_data"
    cached = global_cache.get(cache_key)
    
    if cached is not None:
        return cached

    procs = {}
    # Use memory_percent over the heavy get_memory_info if possible
    for p in psutil.process_iter(['pid','name','username','memory_percent']):
        try:
            info = p.info
            pid = info["pid"]
            cpu = p.cpu_percent(interval=None)
            mem = info["memory_percent"] or 0.0
            
            procs[pid] = {
                "pid": pid,
                "name": info["name"] or "Unknown",
                "user": info["username"] or "System",
                "cpu": cpu,
                "mem": mem
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
            continue
            
    # Cache for 1.0 second (Rate Limiting ~1 FPS)
    global_cache.set(cache_key, procs, ttl=1.0)
    return procs
