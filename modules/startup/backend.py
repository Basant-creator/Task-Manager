# modules/startup/backend.py
import platform
import os
apps = []

if platform.system().lower() == "windows":
    try:
        import winreg
    except Exception:
        winreg = None

def list_startup_apps():
    result = []
    system = platform.system().lower()
    if system == "windows" and winreg:
        keys = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
        ]
        for hive, path in keys:
            try:
                reg = winreg.OpenKey(hive, path)
            except Exception:
                continue
            idx = 0
            while True:
                try:
                    name, cmd, _ = winreg.EnumValue(reg, idx)
                    result.append({"name": name, "command": cmd, "location": f"{hive}\\{path}", "enabled": True, "hive": hive, "path": path})
                except OSError:
                    break
                idx += 1
    elif system == "linux":
        conf = os.path.expanduser("~/.config/autostart")
        if os.path.isdir(conf):
            for f in os.listdir(conf):
                if f.endswith(".desktop"):
                    p = os.path.join(conf, f)
                    result.append({"name": f.replace(".desktop",""), "command": p, "location": p, "enabled": True})
    return result

def disable_startup(app):
    if platform.system().lower() == "windows" and winreg and app.get("name"):
        try:
            reg = winreg.OpenKey(app["hive"], app["path"], 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(reg, app["name"])
            return True
        except Exception:
            return False
    return False

def enable_startup(name, cmd):
    if platform.system().lower() == "windows" and winreg:
        try:
            reg = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(reg, name, 0, winreg.REG_SZ, cmd)
            return True
        except Exception:
            return False
    return False
