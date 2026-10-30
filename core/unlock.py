"""Bootloader capability diagnostics. This module never unlocks or bypasses OEM controls."""
from urllib.parse import urlparse

VENDOR_GUIDES = {
    "google": {
        "name": "Google Pixel",
        "url": "https://developers.google.com/android/images",
        "note": "Check the exact Pixel model and carrier variant. Some carrier models cannot be bootloader-unlocked."
    },
    "motorola": {
        "name": "Motorola",
        "url": "https://en-us.support.motorola.com/app/standalone/bootloader/unlock-your-device-a",
        "note": "Use Motorola's official unlock eligibility page for the exact model. Eligibility is not inferred by this app."
    },
    "xiaomi": {
        "name": "Xiaomi",
        "url": "https://www.mi.com/global/",
        "note": "Unlocking requirements depend on account, region, device and current Xiaomi policy. Use Xiaomi's official Mi Unlock process."
    },
    "oneplus": {
        "name": "OnePlus",
        "url": "https://www.oneplus.com/",
        "note": "Unlock procedure varies by model, region and carrier. Verify the exact model's official instructions."
    },
    "samsung": {
        "name": "Samsung",
        "url": "https://www.samsung.com/",
        "note": "OEM unlocking availability varies by model, region and carrier. Samsung devices do not share one universal Fastboot unlock flow."
    },
}

def assess_unlock(device, fastboot=None):
    manufacturer = (device or {}).get("manufacturer", "").strip().lower()
    vendor = next((v for key, v in VENDOR_GUIDES.items() if key in manufacturer), None)
    props = (device or {}).get("oem_unlock_supported", "Unknown")
    bootloader = (fastboot or {}).get("bootloader", "Unknown")
    if "unlocked" in bootloader.lower() and "not" not in bootloader.lower():
        state = "Already reports unlocked"
    elif props.lower() in ("1", "true", "yes"):
        state = "OEM unlock capability reported by Android; manufacturer eligibility still unverified"
    elif props.lower() in ("0", "false", "no"):
        state = "Android reports OEM unlock unsupported"
    else:
        state = "Unknown — exact manufacturer policy must be checked"
    return {
        "manufacturer_profile": vendor or {"name": manufacturer or "Unknown", "url": "", "note": "No verified vendor-specific guidance is configured."},
        "device_signal": state,
        "can_unlock": None,
        "automatic_unlock": False,
        "warning": "The app cannot determine server-side eligibility or unlock automatically. Official unlocking may erase all user data."
    }
