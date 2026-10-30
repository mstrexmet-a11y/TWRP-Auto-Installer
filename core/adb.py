import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "platform-tools"

def executable(name):
    suffix = ".exe" if __import__("os").name == "nt" else ""
    local = TOOLS / (name + suffix)
    return str(local) if local.exists() else name

def command(args, timeout=15):
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return 1, str(exc)

def adb_devices():
    code, out = command([executable("adb"), "devices"])
    if code:
        return []
    found = []
    for line in out.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            found.append(parts[0])
    return found

def read_device():
    devices = adb_devices()
    if not devices:
        return None
    serial = devices[0]
    props = {
        "model": "ro.product.model",
        "manufacturer": "ro.product.manufacturer",
        "codename": "ro.product.device",
        "android": "ro.build.version.release",
        "build": "ro.build.display.id",
    }
    data = {"serial": serial, "mode": "ADB"}
    for key, prop in props.items():
        _, value = command([executable("adb"), "-s", serial, "shell", "getprop", prop])
        data[key] = value.strip().splitlines()[0] if value.strip() else "Unknown"
    return data

def read_fastboot():
    code, out = command([executable("fastboot"), "devices"])
    devices = [line.split()[0] for line in out.splitlines() if line.split()]
    if not devices:
        return None
    serial = devices[0]
    _, unlocked = command([executable("fastboot"), "getvar", "unlocked"])
    _, secure = command([executable("fastboot"), "getvar", "secure"])
    text = (unlocked + " " + secure).lower()
    if "unlocked: yes" in text or "unlocked: true" in text:
        state = "Unlocked (reported by Fastboot)"
    elif "unlocked: no" in text or "unlocked: false" in text:
        state = "Locked (reported by Fastboot)"
    else:
        state = "Unknown — device does not expose a clear status"
    return {"serial": serial, "mode": "Fastboot", "bootloader": state, "raw": unlocked + secure}
