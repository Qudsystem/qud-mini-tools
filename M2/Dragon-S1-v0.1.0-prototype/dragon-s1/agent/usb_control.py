from __future__ import annotations

import ctypes
import platform

from config import settings


def is_admin() -> bool:
    import os
    if platform.system() == "Windows":
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False
    else:
        # On Linux/macOS, check if running as root (UID 0)
        return os.getuid() == 0


def set_usb_storage_enabled(enabled: bool) -> tuple[bool, str]:
    if not settings.hardware_usb_control:
        return True, "Logical demo mode; hardware control was not changed."
    
    if platform.system() == "Windows":
        if not is_admin():
            return False, "Run the agent as Administrator to change USBSTOR policy."
        try:
            import winreg
            path = r"SYSTEM\CurrentControlSet\Services\USBSTOR"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "Start", 0, winreg.REG_DWORD, 3 if enabled else 4)
            return True, "USB storage enabled." if enabled else "USB storage blocked. Reconnect the device to apply."
        except Exception as exc:
            return False, f"USB control failed: {exc}"
            
    elif platform.system() == "Linux":
        if not is_admin():
            return False, "Run the agent as root (sudo) to control USB on Linux."
        try:
            import subprocess
            import os
            if enabled:
                # Enable usb-storage module
                subprocess.run(["modprobe", "usb-storage"], check=True, stderr=subprocess.DEVNULL)
                # Set authorized_default to 1 for all USB buses
                for usb_host in os.listdir("/sys/bus/usb/devices/"):
                    if usb_host.startswith("usb"):
                        auth_path = f"/sys/bus/usb/devices/{usb_host}/authorized_default"
                        if os.path.exists(auth_path):
                            with open(auth_path, "w") as f:
                                f.write("1")
                return True, "USB storage enabled on Linux."
            else:
                # Block new devices by default
                for usb_host in os.listdir("/sys/bus/usb/devices/"):
                    if usb_host.startswith("usb"):
                        auth_path = f"/sys/bus/usb/devices/{usb_host}/authorized_default"
                        if os.path.exists(auth_path):
                            with open(auth_path, "w") as f:
                                f.write("0")
                # Unbind existing storage devices
                storage_driver_dir = "/sys/bus/usb/drivers/usb-storage"
                if os.path.exists(storage_driver_dir):
                    for dev in os.listdir(storage_driver_dir):
                        if ":" in dev:
                            unbind_path = os.path.join(storage_driver_dir, "unbind")
                            try:
                                with open(unbind_path, "w") as f:
                                    f.write(dev)
                            except Exception:
                                pass
                # Try to unload the module
                subprocess.run(["modprobe", "-r", "usb-storage"], stderr=subprocess.DEVNULL)
                return True, "USB storage blocked on Linux."
        except Exception as exc:
            return False, f"Linux USB control failed: {exc}"
            
    else:
        return False, f"Hardware USB control is not supported on {platform.system()}."
