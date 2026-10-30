# TWRP Auto Installer

A Windows desktop assistant for Android device diagnostics and cautious TWRP discovery.

## Implemented in the current MVP

- ADB device detection and reading manufacturer, model, codename, Android version, build ID and Android's `ro.oem_unlock_supported` signal.
- Fastboot device detection and reading the bootloader state when the device exposes it.
- OEM unlock guidance for Google, Motorola, Xiaomi, OnePlus and Samsung, with links to manufacturer sites.
- Search of the official TWRP device directory.
- A second check that fetches each candidate device page and looks for both the detected codename and model.
- Download of a selected `.img` linked from an official TWRP device page.
- Local SHA-256 calculation after download.
- Windows packaging through GitHub Actions.

## Important limitations — read before use

This is **not yet a universal bootloader unlocker or recovery flasher**.

- **Automatic bootloader unlocking is not implemented.** Unlock eligibility is often decided by a manufacturer's servers, account, carrier, region and exact device variant. Android properties cannot prove that a device is eligible. This app reports device signals and official guidance only; it does not bypass OEM restrictions or issue unlock commands.
- **Exact TWRP page checking is a filter, not a compatibility guarantee.** A page mentioning the model and codename does not prove that every regional/hardware revision is supported. Always compare the full model number and maintainer instructions.
- **Recovery download is implemented**, but the app calculates a local SHA-256 only. It does not claim publisher verification unless a trusted published checksum is separately confirmed.
- **Flashing/installing TWRP is not implemented.** Android devices use different partition layouts and installation procedures (A/B, recovery-as-boot, vendor-specific download modes, dynamic partitions, etc.). Guessing a partition or running a generic flash command can make a device unbootable. A safe installer needs a verified per-device installation profile and explicit user confirmation.
- **All-manufacturer/all-device support is not implemented.** The current vendor guidance covers five common manufacturers, while TWRP discovery checks the official public directory. It cannot find every community build or every device ever made.

If the app cannot establish a safe match, it disables recovery download rather than guessing.

## Requirements

- Windows 10/11
- Python 3.11+
- Android SDK Platform Tools (ADB and Fastboot)

Download Platform Tools from Google's official page: https://developer.android.com/tools/releases/platform-tools

Extract the package and copy `adb.exe` and `fastboot.exe` into `platform-tools/` beside `main.py`. Enable USB debugging and authorize the computer. For Fastboot detection, boot the device into its bootloader screen.

## Run from source

```powershell
py -3.11 -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
python main.py
```

## Safety

- Unlocking commonly erases all user data. Back up first.
- Never flash an image unless the exact device variant and maintainer installation instructions match.
- Some devices cannot be unlocked or have no TWRP build.
- Samsung devices generally use a different flashing workflow; do not assume Fastboot support.

## License

MIT
