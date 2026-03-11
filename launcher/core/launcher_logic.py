# Hunter-Launcher
# Copyright (C) 2026 Caio Monteiro
#
# Este programa é um software livre: você pode redistribuí-lo e/ou modificá-lo 
# sob os termos da Licença Pública Geral GNU (GPL), conforme publicada pela 
# Free Software Foundation, versão 3 da licença, ou (a seu critério) qualquer 
# versão posterior.
#
# Este programa é distribuído na esperança de que seja útil, mas SEM QUALQUER 
# GARANTIA; sem mesmo a garantia implícita de COMERCIALIZAÇÃO ou ADEQUAÇÃO A 
# UM PROPÓSITO ESPECÍFICO. Veja a Licença Pública Geral GNU para mais detalhes.
#
# Você deve ter recebido uma cópia da Licença Pública Geral GNU junto com 
# este programa. Se não, veja: https://www.gnu.org/licenses/
#
# Projeto disponível em: https://github.com/CaioMonteir0/Hunter-Launcher




import os
import ctypes
import subprocess
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
        if not self._window: return
        
        
        sw, sh = get_work_area()
        
        if self._window.width >= sw and self._window.height >= sh:
            
            self._window.resize(1200, 800)
           
            cx = int((ctypes.windll.user32.GetSystemMetrics(0) - 1200) / 2)
            cy = int((ctypes.windll.user32.GetSystemMetrics(1) - 800) / 2)
            self._window.move(cx, cy)
        else:
            # Maximiza respeitando a barra de tarefas
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
        
    def _resolve_shortcut(self, path):
        
        if path.lower().endswith('.lnk'):
            try:
                shell = win32com.client.Dispatch("WScript.Shell")
                shortcut = shell.CreateShortcut(path)
                return shortcut.TargetPath
            except Exception as e:
                print(f"Erro ao resolver atalho: {e}")
                return path
        return path