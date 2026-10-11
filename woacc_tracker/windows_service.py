"""Windows service controls; never import the desktop from the service."""
import ctypes
import subprocess
import sys
from pathlib import Path

SERVICE_NAME = "WOACCTracker"
PARAMETERS_KEY = rf"SYSTEM\CurrentControlSet\Services\{SERVICE_NAME}\Parameters"


def service_status():
    if sys.platform != "win32":
        return "unavailable"
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, rf"SYSTEM\CurrentControlSet\Services\{SERVICE_NAME}"):
            pass
    except FileNotFoundError:
        return "not_installed"
    try:
        import win32serviceutil
        state = win32serviceutil.QueryServiceStatus(SERVICE_NAME)[1]
    except ImportError:
        # Desktop distributions can query through the system command as well.
        result = subprocess.run(["sc.exe", "query", SERVICE_NAME], capture_output=True,
                                text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        import re
        match = re.search(r":\s*([1-7])\s", result.stdout)
        state = int(match.group(1)) if match else 0
    except Exception:
        return "unknown"
    return {1: "stopped", 2: "starting", 3: "stopping", 4: "running"}.get(state, "unknown")


def service_config_path():
    import winreg
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, PARAMETERS_KEY) as key:
        return Path(winreg.QueryValueEx(key, "ConfigPath")[0]).resolve()


def engine_path():
    directory = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[2] / "dist_service" / "WOACC Tracker"
    path = directory / "WOACC Tracker Engine" / "WOACC Tracker Engine.exe"
    if not path.is_file():
        raise FileNotFoundError("WOACC Tracker Engine.exe missing. Install the complete service distribution.")
    return path


def run_service_action(action, config_path):
    """Wait for the elevated engine and propagate cancellation or command failure."""
    import ctypes.wintypes as wt

    class ShellExecuteInfo(ctypes.Structure):
        _fields_ = [("cbSize", wt.DWORD), ("fMask", wt.ULONG), ("hwnd", wt.HWND),
                    ("lpVerb", wt.LPCWSTR), ("lpFile", wt.LPCWSTR), ("lpParameters", wt.LPCWSTR),
                    ("lpDirectory", wt.LPCWSTR), ("nShow", ctypes.c_int), ("hInstApp", wt.HINSTANCE),
                    ("lpIDList", ctypes.c_void_p), ("lpClass", wt.LPCWSTR), ("hkeyClass", wt.HKEY),
                    ("dwHotKey", wt.DWORD), ("hIcon", wt.HANDLE), ("hProcess", wt.HANDLE)]

    executable = engine_path()
    info = ShellExecuteInfo()
    info.cbSize, info.fMask = ctypes.sizeof(info), 0x40
    info.lpVerb, info.lpFile = "runas", str(executable)
    info.lpParameters = subprocess.list2cmdline(["--action", action, "--config", str(config_path)])
    info.lpDirectory, info.nShow = str(executable.parent), 0
    shell = ctypes.WinDLL("shell32", use_last_error=True)
    shell.ShellExecuteExW.argtypes = [ctypes.POINTER(ShellExecuteInfo)]
    if not shell.ShellExecuteExW(ctypes.byref(info)):
        raise ctypes.WinError(ctypes.get_last_error())
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.WaitForSingleObject.argtypes = [wt.HANDLE, wt.DWORD]
    kernel.GetExitCodeProcess.argtypes = [wt.HANDLE, ctypes.POINTER(wt.DWORD)]
    kernel.CloseHandle.argtypes = [wt.HANDLE]
    try:
        wait = kernel.WaitForSingleObject(info.hProcess, 120000)
        if wait == 0x102:
            raise TimeoutError("Windows service command is still pending. Check service-control.log and the service status before retrying.")
        if wait != 0:
            raise ctypes.WinError(ctypes.get_last_error())
        code = wt.DWORD()
        if not kernel.GetExitCodeProcess(info.hProcess, ctypes.byref(code)):
            raise ctypes.WinError(ctypes.get_last_error())
        if code.value:
            raise RuntimeError(f"Service command failed ({code.value}). Check service-control.log.")
    finally:
        kernel.CloseHandle(info.hProcess)
