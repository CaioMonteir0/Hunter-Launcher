import requests, traceback
from urllib.parse import quote
import uuid, os

class SearchApi:
    def __init__(self, parent_api, game_name):
        self.parent = parent_api
        self.game_name = game_name
        settings = self.parent.get_settings()
        self.api_key = settings.get("steamgrid_key", "")
        self.base_url = "https://www.steamgriddb.com/api/v2"

    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "HunterLauncher/1.0 (Windows; SteamGridDB API Integration)"
        }
        
    def notify(self, message, level="error"):
        print(f"[SearchApi] {level.upper()}: {message}")

        if hasattr(self.parent, "notify"):
            self.parent.notify(message, level)
        

    def search_steamgrid(self, query):
        """Busca capas usando a lógica de filtragem manual de proporção."""
        if not self.api_key:
            print("Erro: API Key ausente.")
            self.notify(f"window.showNotification('API Key ausente.', 'error')")
            return []

        try:
            # 1. Autocomplete - Busca o ID do jogo
            safe_query = quote(query)
            search_url = f"{self.base_url}/search/autocomplete/{safe_query}"
            response = requests.get(search_url, headers=self._get_headers())
            
            if response.status_code == 401:
                print("[SteamGridDB] API Key inválida (401)")
                self.notify("API Key inválida. Verifique nas configurações.", "error")
                return []

            if response.status_code == 403:
                print("[SteamGridDB] Acesso negado (403)")
                self.notify("Acesso negado pela API. Verifique sua chave.", "error")
                return []

            response.raise_for_status()
            
            search_data = response.json()

            if not search_data.get('success') or not search_data.get('data'):
                return []

            game_id = search_data['data'][0]['id']
            print(f"ID encontrado: {game_id} para o jogo {search_data['data'][0]['name']}")

            # 2. Busca de Grids - Tentativa com estilo alternate
            grids_url = f"{self.base_url}/grids/game/{game_id}"
            params = {'styles': 'alternate'}

            grids_response = requests.get(grids_url, headers=self._get_headers(), params=params)
            grids_data = grids_response.json()

            # Se falhar, tenta sem filtros de estilo
            if not grids_data.get('success'):
                grids_response = requests.get(grids_url, headers=self._get_headers())
                grids_data = grids_response.json()

            if not grids_data.get('success'):
                return []

            # 3. Filtragem manual por proporção (Vertical)
            urls = []
            for grid in grids_data.get('data', []):
                # Se a altura for maior que a largura, é uma capa estilo "pôster"
                if grid.get('height', 0) > grid.get('width', 0):
                    urls.append(grid.get('url'))
            
            print(f"Sucesso! Capas verticais encontradas: {len(urls)}")
            return urls

        except requests.exceptions.Timeout as e:
            print("[SteamGridDB] Timeout:", e)
            traceback.print_exc()
            self.notify(f"window.showNotification('Tempo de resposta excedido.', 'error')")
            return []

        except requests.exceptions.ConnectionError as e:
            print("[SteamGridDB] ConnectionError:", e)
            traceback.print_exc()
            self.notify(f"window.showNotification('Erro de conexão com SteamGridDB.', 'error')")
            return []

        except Exception as e:
            print("[SteamGridDB] Erro inesperado:", e)
            traceback.print_exc()
            
            self.notify(f"window.showNotification('Erro inesperado ao buscar capas.', 'error')")
            return []

    def download_and_save_cover(self, url):
        """Baixa a imagem e salva no diretório de capas do AppData."""
        try:
            ext = url.split('.')[-1].split('?')[0]
            if len(ext) > 4: ext = 'jpg'
            filename = f"cover_{uuid.uuid4().hex[:8]}.{ext}"
            save_path = os.path.join(self.parent.covers_dir, filename)

            res = requests.get(url, timeout=15)
            if res.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(res.content)
                return save_path
            return None
        except Exception as e:
            print(f"Erro no download: {e}")
            traceback.print_exc()
            self.notify(f"window.showNotification('Erro ao baixar capa.', 'error')")
            return None

    def select_online_cover(self, url):
        local_path = self.download_and_save_cover(url)
        if local_path:
            self.parent.update_game_cover(self.game_name, local_path)
            new_base64 = self.parent._get_image_base64(local_path)
            
            if self.parent._window:
                self.notify(f"window.updateCardImage('{self.game_name}', '{new_base64}')")
                self.notify(f"window.showNotification('Capa de {self.game_name} atualizada!', 'success')")
            
            # --- SOLUÇÃO PARA FECHAR ---
            # Procuramos a janela de busca na lista de janelas do webview e a fechamos
            import webview
            for win in webview.windows:
                if f"Buscar Capa: {self.game_name}" in win.title:
                    win.destroy() # Fecha a janela de busca forçadamente
                    break
            
            self.parent._load_db() # Recarrega o banco para garantir que as mudanças sejam refletidas
                    
            return True
        return False
    
    def validate_api_key(self, api_key):
   

        headers = {
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "HunterLauncher/1.0"
        }

        try:
            response = requests.get(
                "https://www.steamgriddb.com/api/v2/search/autocomplete/test",
                headers=headers,
                timeout=5
            )

            if response.status_code in (401, 403):
                print("[SteamGridDB] Key inválida:", response.status_code)
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