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
import base64
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

class DatabaseManager:
    def __init__(self):
        self.app_data_path = os.path.join(os.getenv('APPDATA'), 'HunterLauncher')
        self.db_path = os.path.join(self.app_data_path, 'games.json')
        self.covers_dir = os.path.join(self.app_data_path, 'covers')
        self.no_cover_path = os.path.join(self.covers_dir, 'no_cover.png')
        
        Path(self.app_data_path).mkdir(parents=True, exist_ok=True)
        Path(self.covers_dir).mkdir(parents=True, exist_ok=True)
        self._ensure_default_cover()

    def _ensure_default_cover(self):
        if not os.path.exists(self.no_cover_path):
            img = Image.new('RGB', (600, 900), color=(15, 23, 42))
            draw = ImageDraw.Draw(img)
            try: font = ImageFont.truetype("arial.ttf", 50)
            except: font = ImageFont.load_default()
            draw.text((160, 420), "SEM IMAGEM", fill=(71, 85, 105), font=font)
            img.save(self.no_cover_path)

    def _load_db(self):
        if not os.path.exists(self.db_path): return []
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return []

    def _save_db(self, games):
        # debug
        import traceback
        print("--- [DEBUG] SALVANDO NO BANCO ---")
        traceback.print_stack(limit=3)
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(games, f, indent=4, ensure_ascii=False)

    def _get_image_base64(self, image_path):
        try:
            clean_path = image_path.replace('file:///', '').replace('/', os.sep)
            if not os.path.exists(clean_path): clean_path = self.no_cover_path
            with Image.open(clean_path) as img:
                img.thumbnail((300, 450))
                buffered = BytesIO()
                img.save(buffered, format="PNG")
                return f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode()}"
        except: return ""
        
        
    def rename_game_alias(self, game_name, alias_name):
        try:
            games = self._load_db()
            for g in games:
                if g['name'] == game_name:
                    g['alias'] = alias_name
            self._save_db(games)
            return True
        except: return False