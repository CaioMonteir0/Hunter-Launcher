# Hunter-Launcher
# Copyright (C) 2026 Caio Monteiro
#
# Projeto disponivel em: https://github.com/CaioMonteir0/Hunter-Launcher

import ctypes
import json
import os
import re
import threading
import time
from ctypes import wintypes

import win32com.client


LAUNCHER_MARKERS = {
    "steam": (
        "steam_appid.txt",
        "steam_api",
        "steamclient",
        "steamworks",
    ),
    "epic": (
        ".egstore",
        "epicgameslauncher",
        "eossdk",
        "epic_online_services",
    ),
    "gog": (
        "goggame-",
        "galaxy",
        "gog",
    ),
    "ubisoft": (
        "uplay_r1_loader",
        "ubisoftconnect",
        "ubisoft",
    ),
    "ea": (
        "eadesktop",
        "ea app",
        "origin",
        "eaanticheat",
    ),
    "rockstar": (
        "socialclub",
        "rockstar",
    ),
    "battlenet": (
        "battle.net",
        "blizzard",
    ),
}

LAUNCHER_PATHS = {
    "steam": (
        ("ProgramFiles(x86)", "Steam", "steam.exe"),
        ("ProgramFiles", "Steam", "steam.exe"),
    ),
    "epic": (
        ("ProgramFiles(x86)", "Epic Games", "Launcher", "Portal", "Binaries", "Win64", "EpicGamesLauncher.exe"),
        ("ProgramFiles", "Epic Games", "Launcher", "Portal", "Binaries", "Win64", "EpicGamesLauncher.exe"),
    ),
    "gog": (
        ("ProgramFiles(x86)", "GOG Galaxy", "GalaxyClient.exe"),
        ("ProgramFiles", "GOG Galaxy", "GalaxyClient.exe"),
    ),
    "ubisoft": (
        ("ProgramFiles(x86)", "Ubisoft", "Ubisoft Game Launcher", "UbisoftConnect.exe"),
        ("ProgramFiles", "Ubisoft", "Ubisoft Game Launcher", "UbisoftConnect.exe"),
    ),
    "ea": (
        ("ProgramFiles", "Electronic Arts", "EA Desktop", "EA Desktop", "EADesktop.exe"),
        ("ProgramFiles(x86)", "Origin", "Origin.exe"),
        ("ProgramFiles", "Origin", "Origin.exe"),
    ),
    "rockstar": (
        ("ProgramFiles", "Rockstar Games", "Launcher", "Launcher.exe"),
        ("ProgramFiles(x86)", "Rockstar Games", "Launcher", "Launcher.exe"),
    ),
    "battlenet": (
        ("ProgramFiles(x86)", "Battle.net", "Battle.net Launcher.exe"),
        ("ProgramFiles", "Battle.net", "Battle.net Launcher.exe"),
    ),
}

LAUNCHER_PROCESS_NAMES = {
    "steam": ("steam.exe",),
    "epic": ("epicgameslauncher.exe",),
    "gog": ("galaxyclient.exe",),
    "ubisoft": ("ubisoftconnect.exe", "upc.exe"),
    "ea": ("eadesktop.exe", "origin.exe"),
    "rockstar": ("launcher.exe", "rockstarservice.exe"),
    "battlenet": ("battle.net launcher.exe", "battle.net.exe"),
}


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
            normalized_path = self._normalize_game_path(exe_path)
            if not os.path.exists(exe_path):
                print(f"Executavel nao encontrado: {exe_path}")
                return False
            if normalized_path in self._running_games:
                return True

            source = self._get_or_detect_game_source(exe_path)
            launcher_status = self._open_platform_launcher(source)
            if launcher_status == "not_found":
                print(f"Launcher da plataforma nao instalado/encontrado, iniciando jogo direto: {source}")
            elif not launcher_status:
                print(f"Launcher da plataforma nao confirmado: {source}")
                return False

            game_dir = os.path.dirname(exe_path)
            known_game_pids = self._find_game_process_ids(exe_path, game_dir)
            process_handle = None

            if source == "steam":
                steam_appid = self._find_steam_appid(exe_path)
                if steam_appid:
                    print(f"Iniciando jogo pela Steam: steam://rungameid/{steam_appid}")
                    self._launch_uri(f"steam://rungameid/{steam_appid}")
                else:
                    print("Manifesto Steam nao encontrado para este jogo, iniciando executavel direto.")
                    process_handle = self._launch_with_process_handle(exe_path, game_dir)
            else:
                process_handle = self._launch_with_process_handle(exe_path, game_dir)

            game_pids = self._wait_for_game_processes(exe_path, game_dir, known_game_pids)
            if game_pids:
                self._start_playtime_monitor(exe_path, game_dir, game_pids, process_handle)
            elif process_handle:
                self._start_playtime_monitor(exe_path, game_dir, set(), process_handle)
            return True
        except Exception as e:
            print(f"Erro ao lancar: {e}")
            return False

    def stop_game(self, path):
        try:
            normalized_path = self._normalize_game_path(path)
            running_game = self._running_games.get(normalized_path)
            if not running_game:
                return False

            pids = set(running_game.get("pids", ()))
            game_dir = running_game.get("game_dir")
            if game_dir:
                pids.update(self._find_game_process_ids(path, game_dir))

            stopped = False
            for pid in list(pids):
                stopped = self._terminate_process(pid) or stopped

            handle = running_game.get("handle")
            if handle and not stopped:
                stopped = bool(ctypes.windll.kernel32.TerminateProcess(handle, 1))

            return stopped

        except Exception as e:
            print(f"Erro ao encerrar jogo: {e}")
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

    def detect_game_source(self, path):
        exe_path = os.path.abspath(path)
        game_dir = os.path.dirname(exe_path)
        scores = {source: 0 for source in LAUNCHER_MARKERS}
        scanned = 0
        max_files = 5000
        max_depth = 4

        if not os.path.isdir(game_dir):
            return {"source": "unknown", "confidence": 0}

        for dirpath, dirnames, filenames in os.walk(game_dir):
            rel_path = os.path.relpath(dirpath, game_dir)
            depth = 0 if rel_path == "." else rel_path.count(os.sep) + 1
            if depth > max_depth:
                dirnames[:] = []
                continue

            names = [name.lower() for name in dirnames + filenames]
            for name in names:
                scanned += 1
                if scanned > max_files:
                    break

                for source, markers in LAUNCHER_MARKERS.items():
                    for marker in markers:
                        if marker in name:
                            scores[source] += 2

                if name == ".egstore":
                    scores["epic"] += 10
                elif name == "steam_appid.txt":
                    scores["steam"] += 10
                elif name.startswith("goggame-") and name.endswith(".info"):
                    scores["gog"] += 10
                elif name.startswith("uplay_r1_loader"):
                    scores["ubisoft"] += 10
                elif name in ("socialclub.dll", "socialclub64.dll"):
                    scores["rockstar"] += 10

            if scanned > max_files:
                break

        source, confidence = max(scores.items(), key=lambda item: item[1])
        if confidence <= 0:
            return {"source": "unknown", "confidence": 0}

        return {"source": source, "confidence": confidence}

    def _get_or_detect_game_source(self, exe_path):
        normalized_path = self._normalize_game_path(exe_path)
        detected = {"source": "unknown", "confidence": 0}

        if hasattr(self, "_load_db"):
            games = self._load_db()
            for game in games:
                if self._normalize_game_path(game.get("path", "")) == normalized_path:
                    current_source = game.get("source", "unknown")
                    if current_source and current_source != "unknown":
                        return current_source

                    detected = self.detect_game_source(exe_path)
                    game["source"] = detected["source"]
                    game["source_confidence"] = detected["confidence"]
                    if hasattr(self, "_save_db"):
                        self._save_db(games)
                    return detected["source"]

        detected = self.detect_game_source(exe_path)
        return detected["source"]

    def _open_platform_launcher(self, source):
        if not source or source == "unknown":
            return True

        launcher_path = self._find_launcher_path(source)
        if not launcher_path:
            print(f"Launcher da plataforma nao encontrado: {source}")
            return "not_found"

        if self._is_launcher_running(source, launcher_path):
            return True

        result = ctypes.windll.shell32.ShellExecuteW(
            None,
            "open",
            launcher_path,
            None,
            os.path.dirname(launcher_path),
            1,
        )
        if result > 32:
            print(f"Launcher da plataforma aberto: {source}")
            return self._wait_for_launcher(source, launcher_path)

        return False

    def _find_launcher_path(self, source):
        for candidate in LAUNCHER_PATHS.get(source, ()):
            env_name, *parts = candidate
            base_path = os.getenv(env_name)
            if not base_path:
                continue

            launcher_path = os.path.join(base_path, *parts)
            if os.path.exists(launcher_path):
                return launcher_path

        return None

    def _launch_uri(self, uri):
        result = ctypes.windll.shell32.ShellExecuteW(None, "open", uri, None, None, 1)
        return result > 32

    def _find_steam_appid(self, exe_path):
        game_dir = os.path.dirname(os.path.abspath(exe_path))
        common_dir = self._find_steam_common_dir(game_dir)
        if not common_dir:
            return ""

        steamapps_dir = os.path.dirname(common_dir)
        game_dir_normalized = self._normalize_game_path(game_dir)

        try:
            for filename in os.listdir(steamapps_dir):
                if not filename.lower().startswith("appmanifest_") or not filename.lower().endswith(".acf"):
                    continue

                manifest_path = os.path.join(steamapps_dir, filename)
                with open(manifest_path, "r", encoding="utf-8", errors="ignore") as manifest:
                    content = manifest.read()

                installdir_match = re.search(r'"installdir"\s+"([^"]+)"', content, re.IGNORECASE)
                appid_match = re.search(r'"appid"\s+"(\d+)"', content, re.IGNORECASE)
                if not installdir_match or not appid_match:
                    continue

                install_dir = os.path.join(common_dir, installdir_match.group(1))
                if game_dir_normalized.startswith(self._normalize_game_path(install_dir)):
                    return appid_match.group(1)
        except Exception as e:
            print(f"Erro ao procurar AppID Steam: {e}")

        return ""

    def _find_steam_common_dir(self, game_dir):
        current_dir = os.path.abspath(game_dir)
        for _ in range(8):
            if os.path.basename(current_dir).lower() == "common":
                steamapps_dir = os.path.dirname(current_dir)
                if os.path.basename(steamapps_dir).lower() == "steamapps":
                    return current_dir

            parent_dir = os.path.dirname(current_dir)
            if parent_dir == current_dir:
                break
            current_dir = parent_dir

        return ""

    def _normalize_game_path(self, path):
        if not path:
            return ""
        return os.path.normcase(os.path.abspath(path)).replace("\\", "/")

    def _iter_processes(self):
        process_ids = self._enum_process_ids()
        for pid in process_ids:
            process_path = self._get_process_image_path(pid)
            if not process_path:
                continue

            yield {
                "pid": pid,
                "name": os.path.basename(process_path).lower(),
                "path": self._normalize_game_path(process_path),
            }

    def _enum_process_ids(self):
        psapi = ctypes.windll.psapi
        process_count = 4096

        while True:
            process_ids = (wintypes.DWORD * process_count)()
            bytes_returned = wintypes.DWORD()
            buffer_size = ctypes.sizeof(process_ids)

            if not psapi.EnumProcesses(
                ctypes.byref(process_ids),
                buffer_size,
                ctypes.byref(bytes_returned),
            ):
                return []

            count = bytes_returned.value // ctypes.sizeof(wintypes.DWORD)
            if count < process_count:
                return [int(process_ids[index]) for index in range(count) if process_ids[index]]

            process_count *= 2

    def _get_process_image_path(self, pid):
        process_query_limited_information = 0x1000
        handle = ctypes.windll.kernel32.OpenProcess(
            process_query_limited_information,
            False,
            int(pid),
        )
        if not handle:
            return ""

        try:
            size = wintypes.DWORD(32768)
            buffer = ctypes.create_unicode_buffer(size.value)
            if ctypes.windll.kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
                return buffer.value
            return ""
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)

    def _is_launcher_running(self, source, launcher_path):
        launcher_names = set(LAUNCHER_PROCESS_NAMES.get(source, ()))
        launcher_names.add(os.path.basename(launcher_path).lower())
        normalized_launcher_path = self._normalize_game_path(launcher_path)

        for process in self._iter_processes():
            if process["path"] == normalized_launcher_path or process["name"] in launcher_names:
                return True

        return False

    def _wait_for_launcher(self, source, launcher_path, timeout=30):
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self._is_launcher_running(source, launcher_path):
                return True
            time.sleep(0.5)

        return False

    def _find_game_process_ids(self, exe_path, game_dir):
        normalized_exe = self._normalize_game_path(exe_path)
        normalized_dir = self._normalize_game_path(game_dir).rstrip("/") + "/"
        process_ids = set()

        for process in self._iter_processes():
            process_path = process["path"]
            if process_path == normalized_exe or process_path.startswith(normalized_dir):
                process_ids.add(process["pid"])

        return process_ids

    def _wait_for_game_processes(self, exe_path, game_dir, known_pids, timeout=45):
        deadline = time.time() + timeout
        while time.time() < deadline:
            current_pids = self._find_game_process_ids(exe_path, game_dir)
            new_pids = current_pids - set(known_pids)
            if new_pids:
                return new_pids
            time.sleep(0.5)

        return set()

    def _terminate_process(self, pid):
        process_terminate = 0x0001
        handle = ctypes.windll.kernel32.OpenProcess(process_terminate, False, int(pid))
        if not handle:
            return False

        try:
            return bool(ctypes.windll.kernel32.TerminateProcess(handle, 1))
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)

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

    def _start_playtime_monitor(self, exe_path, game_dir, process_ids, process_handle=None):
        normalized_path = self._normalize_game_path(exe_path)
        if normalized_path in self._running_games:
            return

        game_name = self._get_game_name_by_path(exe_path)
        self._running_games[normalized_path] = {
            "handle": process_handle,
            "name": game_name,
            "path": normalized_path,
            "game_dir": self._normalize_game_path(game_dir),
            "pids": set(process_ids),
        }
        self._notify_game_running(game_name, normalized_path, True)

        def monitor():
            start_time = time.time()
            try:
                quiet_checks = 0
                while True:
                    active_pids = self._find_game_process_ids(exe_path, game_dir)
                    if active_pids:
                        quiet_checks = 0
                        self._running_games[normalized_path]["pids"] = active_pids
                    else:
                        quiet_checks += 1
                        if quiet_checks >= 4:
                            break

                    time.sleep(1)

                elapsed_seconds = max(0, int(time.time() - start_time))
                if elapsed_seconds > 0 and hasattr(self, "record_play_session"):
                    self.record_play_session(normalized_path, elapsed_seconds)
            finally:
                if process_handle:
                    ctypes.windll.kernel32.CloseHandle(process_handle)
                self._running_games.pop(normalized_path, None)
                self._notify_game_running(game_name, normalized_path, False)

        threading.Thread(target=monitor, daemon=True).start()

    def _notify_game_running(self, game_name, path, is_running):
        if not self._window:
            return

        self._window.evaluate_js(
            "window.updateGameRunning && window.updateGameRunning("
            f"{json.dumps(game_name)}, {json.dumps(path)}, {str(is_running).lower()})"
        )

    def _get_game_name_by_path(self, path):
        normalized_path = self._normalize_game_path(path)
        if hasattr(self, "_load_db"):
            for game in self._load_db():
                if self._normalize_game_path(game.get("path", "")) == normalized_path:
                    return game.get("name") or os.path.basename(os.path.dirname(path))

        return os.path.basename(os.path.dirname(path))

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
