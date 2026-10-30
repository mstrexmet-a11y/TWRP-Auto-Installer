# TWRP Auto Installer

A Windows desktop assistant for identifying Android devices, checking bootloader state, and finding **device-specific** TWRP recovery information.

## Current status

This is an early, safety-first MVP. It can:
- Detect an Android device through ADB and read its model, manufacturer, codename and Android version.
- Detect Fastboot mode and inspect the reported bootloader state.
- Search the official TWRP device directory by codename/model.
- Open the official device page so you can verify support and follow its exact installation guide.
- Build a Windows executable with GitHub Actions.

It deliberately does **not** unlock bootloaders or flash images automatically yet. Unlocking commonly wipes user data, manufacturer procedures differ, and an incorrect recovery image can make a device unbootable. ADB/Fastboot values are not always reliable indicators of unlock eligibility.

## Requirements

- Windows 10/11
- Python 3.11+
- Android SDK Platform Tools (ADB and Fastboot)

Download Platform Tools from Google's official page: https://developer.android.com/tools/releases/platform-tools

Extract the package and copy `adb.exe` and `fastboot.exe` into `platform-tools/` beside `main.py`. Enable USB debugging on the phone and authorize the computer. For Fastboot detection, boot the device into its bootloader screen.

## Run from source

```powershell
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Safety notes

- Never use a recovery image unless its device codename and build requirements match exactly.
- Prefer official TWRP downloads and the maintainer's installation instructions.
- Back up important data before any bootloader operation.
- Bootloader unlocking may factory-reset the phone.
- Some devices have no TWRP build or cannot be unlocked.
- Samsung devices generally use a different flashing workflow; do not assume Fastboot support.

## License

MIT
