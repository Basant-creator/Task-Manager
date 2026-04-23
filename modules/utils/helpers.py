# modules/utils/helpers.py
def check_matplotlib():
    try:
        import matplotlib  # noqa: F401
        return True
    except Exception:
        return False

def check_psutil():
    try:
        import psutil  # noqa: F401
        return True
    except Exception:
        return False
