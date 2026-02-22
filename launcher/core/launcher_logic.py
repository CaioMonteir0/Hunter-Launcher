import os
import ctypes
import subprocess

class LauncherLogic:
    def get_folder_size(self, file_path):
        folder = os.path.dirname(file_path)
        total_size = 0
        try:
            for dirpath, _, filenames in os.walk(folder):
                for f in filenames:
                    total_size += os.path.getsize(os.path.join(dirpath, f))
            gb = total_size / (1024**3)
            return f"{gb:.2f} GB" if gb >= 1 else f"{total_size / (1024**2):.1f} MB"
        except: return "0 GB"

    def launch_game(self, path):
        try:
            exe_path = os.path.abspath(path)
            game_dir = os.path.dirname(exe_path)
            ctypes.windll.shell32.ShellExecuteW(None, "runas", exe_path, None, game_dir, 1)
            return True
        except Exception as e:
            print(f"Erro ao lançar: {e}")
            return False