# Hunter-Launcher
# Copyright (C) 2026 Caio Monteiro
#
# Este programa e um software livre: voce pode redistribui-lo e/ou modifica-lo
# sob os termos da Licenca Publica Geral GNU (GPL), conforme publicada pela
# Free Software Foundation, versao 3 da licenca, ou (a seu criterio) qualquer
# versao posterior.
#
# Projeto disponivel em: https://github.com/CaioMonteir0/Hunter-Launcher

import os
import traceback
import uuid
from urllib.parse import quote

import requests


class SearchApi:
    def __init__(self, parent_api, game_name, asset_type="cover"):
        self.parent = parent_api
        self.game_name = game_name
        self.asset_type = asset_type
        settings = self.parent.get_settings()
        self.api_key = settings.get("steamgrid_key", "")
        self.base_url = "https://www.steamgriddb.com/api/v2"

    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "HunterLauncher/1.0 (Windows; SteamGridDB API Integration)",
        }

    def notify(self, message, level="error"):
        print(f"[SearchApi] {level.upper()}: {message}")

        if hasattr(self.parent, "notify"):
            self.parent.notify(message, level)

    def close_search_window(self):
        self.parent.close_search_window(self.game_name)

    def _find_game_id(self, query):
        safe_query = quote(query)
        search_url = f"{self.base_url}/search/autocomplete/{safe_query}"
        response = requests.get(search_url, headers=self._get_headers(), timeout=10)

        if response.status_code == 401:
            print("[SteamGridDB] API Key invalida (401)")
            self.notify("API Key invalida. Verifique nas configuracoes.", "error")
            return None

        if response.status_code == 403:
            print("[SteamGridDB] Acesso negado (403)")
            self.notify("Acesso negado pela API. Verifique sua chave.", "error")
            return None

        response.raise_for_status()
        search_data = response.json()

        if not search_data.get("success") or not search_data.get("data"):
            return None

        game = search_data["data"][0]
        print(f"ID encontrado: {game['id']} para o jogo {game['name']}")
        return game["id"]

    def search_steamgrid(self, query, page=0):
        """Busca capas verticais usando grids do SteamGridDB."""
        if not self.api_key:
            print("Erro: API Key ausente.")
            self.notify("API Key ausente.", "error")
            return {"images": [], "has_next": False}

        try:
            game_id = self._find_game_id(query)
            if not game_id:
                return {"images": [], "has_next": False}

            grids_url = f"{self.base_url}/grids/game/{game_id}"
            params = {
                "styles": "alternate,material,no_logo",
                "limit": 12,
                "page": page,
            }

            grids_response = requests.get(
                grids_url,
                headers=self._get_headers(),
                params=params,
                timeout=10,
            )
            grids_response.raise_for_status()
            grids_data = grids_response.json()

            if not grids_data.get("success"):
                return {"images": [], "has_next": False}

            urls = []
            raw_data = grids_data.get("data", [])

            for grid in raw_data:
                if grid.get("height", 0) > grid.get("width", 0) and grid.get("url"):
                    urls.append(grid.get("url"))

            has_next = len(raw_data) == 12
            print(f"[SteamGridDB] Pagina {page}: {len(urls)} capas verticais encontradas.")

            return {
                "images": urls,
                "has_next": has_next,
            }

        except requests.exceptions.Timeout as e:
            print("[SteamGridDB] Timeout:", e)
            traceback.print_exc()
            self.notify("Tempo de resposta excedido.", "error")
            return {"images": [], "has_next": False}

        except requests.exceptions.ConnectionError as e:
            print("[SteamGridDB] ConnectionError:", e)
            traceback.print_exc()
            self.notify("Erro de conexao com SteamGridDB.", "error")
            return {"images": [], "has_next": False}

        except Exception as e:
            print("[SteamGridDB] Erro inesperado:", e)
            traceback.print_exc()
            self.notify("Erro inesperado ao buscar capas.", "error")
            return {"images": [], "has_next": False}

    def search_steamgrid_banner(self, query):
        """Busca um banner horizontal usando heroes do SteamGridDB."""
        results = self.search_steamgrid_banners(query)
        if results and results.get("images"):
            return results["images"][0]
        return None

    def search_steamgrid_banners(self, query, page=0):
        """Busca banners horizontais usando heroes do SteamGridDB."""
        if not self.api_key:
            print("Erro: API Key ausente.")
            self.notify("API Key ausente.", "error")
            return {"images": [], "has_next": False}

        try:
            game_id = self._find_game_id(query)
            if not game_id:
                return {"images": [], "has_next": False}

            heroes_url = f"{self.base_url}/heroes/game/{game_id}"
            params = {
                "styles": "alternate,material",
                "types": "static",
                "limit": 12,
                "page": page,
            }

            heroes_response = requests.get(
                heroes_url,
                headers=self._get_headers(),
                params=params,
                timeout=10,
            )
            heroes_response.raise_for_status()
            heroes_data = heroes_response.json()

            if not heroes_data.get("success"):
                return {"images": [], "has_next": False}

            urls = []
            raw_data = heroes_data.get("data", [])
            for hero in heroes_data.get("data", []):
                if hero.get("width", 0) > hero.get("height", 0) and hero.get("url"):
                    urls.append(hero.get("url"))

            has_next = len(raw_data) == 12
            print(f"[SteamGridDB] Pagina {page}: {len(urls)} banners encontrados.")

            return {
                "images": urls,
                "has_next": has_next,
            }

        except requests.exceptions.Timeout as e:
            print("[SteamGridDB] Timeout ao buscar banner:", e)
            traceback.print_exc()
            return {"images": [], "has_next": False}

        except requests.exceptions.ConnectionError as e:
            print("[SteamGridDB] ConnectionError ao buscar banner:", e)
            traceback.print_exc()
            return {"images": [], "has_next": False}

        except Exception as e:
            print("[SteamGridDB] Erro inesperado ao buscar banner:", e)
            traceback.print_exc()
            return {"images": [], "has_next": False}

    def download_and_save_image(self, url, prefix, save_dir, error_label="imagem"):
        """Baixa uma imagem e salva localmente no AppData."""
        try:
            ext = url.split(".")[-1].split("?")[0]
            if len(ext) > 4:
                ext = "jpg"

            filename = f"{prefix}_{uuid.uuid4().hex[:8]}.{ext}"
            save_path = os.path.join(save_dir, filename)

            res = requests.get(url, timeout=15)
            if res.status_code == 200:
                with open(save_path, "wb") as f:
                    f.write(res.content)
                return save_path

            return None

        except Exception as e:
            print(f"Erro no download: {e}")
            traceback.print_exc()
            self.notify(f"Erro ao baixar {error_label}.", "error")
            return None

    def download_and_save_cover(self, url):
        """Baixa a imagem e salva no diretorio de capas do AppData."""
        return self.download_and_save_image(
            url,
            "cover",
            self.parent.covers_dir,
            "capa",
        )

    def download_and_save_banner(self, url):
        """Baixa o banner e salva no diretorio de banners do AppData."""
        return self.download_and_save_image(
            url,
            "banner",
            self.parent.banners_dir,
            "banner",
        )

    def select_online_cover(self, url):
        local_path = self.download_and_save_cover(url)
        if local_path:
            self.parent.update_game_cover(self.game_name, local_path)

            if self.parent._window:
                self.notify(f"Capa de {self.game_name} atualizada!", "success")

            import webview

            for win in webview.windows:
                if f"Buscar Capa: {self.game_name}" in win.title:
                    win.destroy()
                    break

            self.parent._window.evaluate_js("window.handleAction('LOAD_LIBRARY')")

            return True
        return False

    def select_online_banner(self, url):
        local_path = self.download_and_save_banner(url)
        if local_path:
            self.parent.update_game_banner(self.game_name, local_path)

            if self.parent._window:
                self.notify(f"Banner de {self.game_name} atualizado!", "success")

            import webview

            for win in webview.windows:
                if self.game_name in win.title:
                    win.destroy()
                    break

            self.parent._window.evaluate_js("window.handleAction('LOAD_LIBRARY')")

            return True
        return False

    def select_online_asset(self, url):
        if self.asset_type == "banner":
            return self.select_online_banner(url)
        return self.select_online_cover(url)

    def validate_api_key(self, api_key):
        headers = {
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "HunterLauncher/1.0",
        }

        try:
            response = requests.get(
                "https://www.steamgriddb.com/api/v2/search/autocomplete/test",
                headers=headers,
                timeout=5,
            )

            if response.status_code in (401, 403):
                print("[SteamGridDB] Key invalida:", response.status_code)
                return False

            if response.status_code != 200:
                print("[SteamGridDB] Status inesperado:", response.status_code)
                return False

            data = response.json()

            if not data.get("success", False):
                print("[SteamGridDB] success=False no JSON")
                return False

            return True

        except Exception as e:
            print("[SteamGridDB] Erro ao validar key:", e)
            return False
