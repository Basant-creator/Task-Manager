# modules/processes/backend.py
import psutil
import threading

def fetch_all_processes():
    procs = []
    for p in psutil.process_iter(['pid','name','username','cpu_percent','memory_percent']):
        try:
            info = p.info
            procs.append(info)
        except Exception:
            continue
    return procs

# simple wrapper to run in background thread
def fetch_in_thread(callback):
    def worker():
        result = fetch_all_processes()
        callback(result)
    t = threading.Thread(target=worker, daemon=True)
    t.start()
    return t
