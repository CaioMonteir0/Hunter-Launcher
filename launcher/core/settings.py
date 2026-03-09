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
import json
import win32crypt
import base64
from pathlib import Path

class SettingsManager:
    
    def encrypt_string(self,plain_text: str) -> str:
        data = plain_text.encode("utf-8")
        encrypted = win32crypt.CryptProtectData(data, None, None, None, None, 0)
        return base64.b64encode(encrypted).decode("utf-8")

    def decrypt_string(self, cipher_text: str) -> str:
        data = base64.b64decode(cipher_text.encode("utf-8"))
        decrypted = win32crypt.CryptUnprotectData(data, None, None, None, 0)[1]
        return decrypted.decode("utf-8")
    
    def __init__(self, app_data_path):
        self.settings_dir = os.path.join(app_data_path, 'settings')
        self.settings_path = os.path.join(self.settings_dir, 'config.json')
        Path(self.settings_dir).mkdir(parents=True, exist_ok=True)
        self._ensure_settings_file()

    def _ensure_settings_file(self):
        if not os.path.exists(self.settings_path):
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump({"steamgrid_key": ""}, f, indent=4)

    def get_settings(self):
        try:
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if "steamgrid_key" in data and data["steamgrid_key"]:
                try:
                    data["steamgrid_key"] = self.decrypt_string(data["steamgrid_key"])
                except:
                    data["steamgrid_key"] = ""

            return data
        except:
            return {"steamgrid_key": ""}

    def save_settings(self, settings_data):
        try:
            if "steamgrid_key" in settings_data and settings_data["steamgrid_key"]:
                settings_data["steamgrid_key"] = self.encrypt_string(settings_data["steamgrid_key"])

            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings_data, f, indent=4)

            return True
        except Exception as e:
            
                print("Erro ao salvar:", e)
                return False