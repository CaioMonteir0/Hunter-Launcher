import os
import ctypes
import subprocess

class LauncherLogic:
    def __init__(self):
        self._window = None

    def set_window(self, window):
        # Armazena a referência da janela do pywebview
        self._window = window

    def minimize(self):
        if self._window:
            self._window.minimize()

    def close(self):
       
        for win in self.all_windows:
            try:
                win.destroy()
            except:
                pass
        
        os._exit(0)

    def toggle_maximize(self):
        if self._window:
            
            self._window.toggle_fullscreen()
            
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