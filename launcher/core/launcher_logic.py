# Hunter-Launcher
# Copyright (C) 2026 Caio Monteiro
#
# Projeto disponivel em: https://github.com/CaioMonteir0/Hunter-Launcher

import ctypes
import os
import threading
import time
from ctypes import wintypes

import win32com.client


def get_work_area():
    user32 = ctypes.windll.user32
    rect = wintypes.RECT()

    user32.SystemParametersInfoW(48, 0, ctypes.byref(rect), 0)
    return rect.right - rect.left, rect.bottom - rect.top


class LauncherLogic:
    def __init__(self):
        self._window = None
        self._running_games = {}

    def set_window(self, window):
        self._window = window

    def minimize(self):
        if self._window:
            self._window.minimize()

    def close(self):
        for win in self.all_windows:
            try:
                win.destroy()
            except Exception:
                pass

        os._exit(0)

    def toggle_maximize(self):
        if not self._window:
            return

        sw, sh = get_work_area()

        if self._window.width >= sw and self._window.height >= sh:
            self._window.resize(1200, 800)

            cx = int((ctypes.windll.user32.GetSystemMetrics(0) - 1200) / 2)
            cy = int((ctypes.windll.user32.GetSystemMetrics(1) - 800) / 2)
            self._window.move(cx, cy)
        else:
            self._window.move(0, 0)
            self._window.resize(sw, sh)

    def get_folder_size(self, file_path):
        folder = os.path.dirname(file_path)
        total_size = 0
        try:
            for dirpath, _, filenames in os.walk(folder):
                for f in filenames:
                    total_size += os.path.getsize(os.path.join(dirpath, f))
            gb = total_size / (1024**3)
            return f"{gb:.2f} GB" if gb >= 1 else f"{total_size / (1024**2):.1f} MB"
        except Exception:
            return "0 GB"

    def launch_game(self, path):
        try:
            exe_path = os.path.abspath(path)
            if not os.path.exists(exe_path):
                print(f"Executavel nao encontrado: {exe_path}")
                return False

            game_dir = os.path.dirname(exe_path)
            process_handle = self._launch_with_process_handle(exe_path, game_dir)
            if process_handle:
                self._start_playtime_monitor(exe_path, process_handle)
            return True
        except Exception as e:
            print(f"Erro ao lancar: {e}")
            return False

    def open_game_location(self, path):
        try:
            exe_path = os.path.normpath(os.path.abspath(path))
            if os.path.exists(exe_path):
                params = f'/select,"{exe_path}"'
                ctypes.windll.shell32.ShellExecuteW(None, "open", "explorer.exe", params, None, 1)
                return True

            game_dir = os.path.dirname(exe_path)
            if os.path.exists(game_dir):
                ctypes.windll.shell32.ShellExecuteW(None, "open", game_dir, None, None, 1)
                return True

            return False
        except Exception as e:
            print(f"Erro ao abrir local do jogo: {e}")
            return False

    def _launch_with_process_handle(self, exe_path, game_dir):
        see_mask_nocloseprocess = 0x00000040
        sw_shownormal = 1

        class SHELLEXECUTEINFO(ctypes.Structure):
            _fields_ = [
                ("cbSize", wintypes.DWORD),
                ("fMask", ctypes.c_ulong),
                ("hwnd", wintypes.HWND),
                ("lpVerb", wintypes.LPCWSTR),
                ("lpFile", wintypes.LPCWSTR),
                ("lpParameters", wintypes.LPCWSTR),
                ("lpDirectory", wintypes.LPCWSTR),
                ("nShow", ctypes.c_int),
                ("hInstApp", wintypes.HINSTANCE),
                ("lpIDList", ctypes.c_void_p),
                ("lpClass", wintypes.LPCWSTR),
                ("hkeyClass", wintypes.HANDLE),
                ("dwHotKey", wintypes.DWORD),
                ("hIcon", wintypes.HANDLE),
                ("hProcess", wintypes.HANDLE),
            ]

        sei = SHELLEXECUTEINFO()
        sei.cbSize = ctypes.sizeof(SHELLEXECUTEINFO)
        sei.fMask = see_mask_nocloseprocess
        sei.hwnd = None
        sei.lpVerb = "open"
        sei.lpFile = exe_path
        sei.lpParameters = None
        sei.lpDirectory = game_dir
        sei.nShow = sw_shownormal

        ok = ctypes.windll.shell32.ShellExecuteExW(ctypes.byref(sei))
        if not ok:
            error_code = ctypes.GetLastError()
            print(f"ShellExecuteEx falhou ({error_code}), tentando ShellExecuteW.")
            result = ctypes.windll.shell32.ShellExecuteW(
                None,
                "open",
                exe_path,
                None,
                game_dir,
                sw_shownormal,
            )
            return None if result <= 32 else None

        return sei.hProcess

    def _start_playtime_monitor(self, exe_path, process_handle):
        normalized_path = exe_path.replace("\\", "/")
        if normalized_path in self._running_games:
            return

        self._running_games[normalized_path] = True

        def monitor():
            start_time = time.time()
            try:
                ctypes.windll.kernel32.WaitForSingleObject(process_handle, 0xFFFFFFFF)
                elapsed_seconds = max(0, int(time.time() - start_time))
                if elapsed_seconds > 0 and hasattr(self, "record_play_session"):
                    self.record_play_session(normalized_path, elapsed_seconds)
            finally:
                ctypes.windll.kernel32.CloseHandle(process_handle)
                self._running_games.pop(normalized_path, None)

        threading.Thread(target=monitor, daemon=True).start()

    def _resolve_shortcut(self, path):
        if path.lower().endswith(".lnk"):
            try:
                shell = win32com.client.Dispatch("WScript.Shell")
                shortcut = shell.CreateShortcut(path)
                return shortcut.TargetPath
            except Exception as e:
                print(f"Erro ao resolver atalho: {e}")
                return path
        return path
