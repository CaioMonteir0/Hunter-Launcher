import os
import webview
import threading
import ctypes, json

# módulos da pasta core
from core.database import DatabaseManager
from core.settings import SettingsManager
from core.launcher_logic import LauncherLogic
from core.cover_manager import CoverManager
from core.search_api import SearchApi


# Função global para pegar a resolução real do Windows
def get_screen_resolution():
    user32 = ctypes.windll.user32
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

def center_initial_window(window):
    
    sw, sh = get_screen_resolution()
    x = int((sw - 480) / 2)
    y = int((sh - 360) / 2)
    window.move(x, y)

webview.settings['DRAG_REGION_DIRECT_TARGET_ONLY'] = True

class Api(DatabaseManager, SettingsManager, LauncherLogic, CoverManager):

    def __init__(self):
    
        # 1. Inicializa o Database primeiro para garantir que self.app_data_path exista
        DatabaseManager.__init__(self)
        # 2. Inicializa os outros módulos
        SettingsManager.__init__(self, self.app_data_path)
        LauncherLogic.__init__(self)
        CoverManager.__init__(self)
        self.all_windows = []
        
        self._window = None

    def set_window(self, window):
        self._window = window
        
        if window not in self.all_windows:
            self.all_windows.append(window)
        
    def add_window(self, window):
       
        self.all_windows.append(window)

    # --- MÉTODOS DE PONTE (JS -> PYTHON) ---
    
    
    def notify(self, message, level="error"):
        print(f"[UI] {level.upper()}: {message}")

        if self._window:
            safe_message = json.dumps(message)
            self._window.evaluate_js(
                f"window.showNotification({safe_message}, '{level}')"
            )

    def get_library(self):
        games = self._load_db()
        display_list = []
        for g in games:
            display_game = g.copy()
            display_game['cover'] = self._get_image_base64(g.get('cover', ''))
            display_list.append(display_game)

        # Thread para baixar capas automáticas
        threading.Thread(target=self._auto_fix_covers, daemon=True).start()
        return display_list

    def add_game(self):
       
        if not self._window: return None

        result = self._window.create_file_dialog(
            webview.FileDialog.OPEN, 
            allow_multiple=False, 
            file_types=('Executáveis (*.exe)',)
        )
        
        if not result: return None

        file_path = result[0].replace('\\', '/')
        game_name = os.path.basename(os.path.dirname(file_path))
        
        new_game = {
            "name": game_name,
            "path": file_path,
            "size": self.get_folder_size(file_path),
            "cover": self.no_cover_path 
        }

        games = self._load_db()
        if any(g['path'] == file_path for g in games): return None
            
        games.append(new_game)
        self._save_db(games)
        
        display_game = new_game.copy()
        display_game['cover'] = self._get_image_base64(self.no_cover_path)
        
        # Tenta buscar a capa assim que adiciona
        threading.Thread(target=self._auto_fix_covers, daemon=True).start()
        self._window.evaluate_js(f"window.showNotification('Jogo adicionado: {game_name}', 'success')")
        return display_game

   
    
    def get_api_settings(self):
        
        return self.get_settings()

    def save_api_settings(self, data):
        
        # Se o usuário estiver tentando salvar a key
        if "steamgrid_key" in data and data["steamgrid_key"]:
            raw_key = data["steamgrid_key"]

            # instância temporária só para validar
            temp_search = SearchApi(self, game_name=None)

            is_valid = temp_search.validate_api_key(raw_key)

            if not is_valid:
                self.notify("API Key inválida. Verifique nas configurações.", "error")
                return False

        # Se passou na validação (ou não havia key), salva normalmente
        result = self.save_settings(data)

        if result:
            self.notify("Configurações salvas com sucesso!", "success")

        return result

  
    
    def delete_game_request(self, game_name, mode):
        """
        mode 'launcher': apenas remove do JSON
        mode 'full': remove do JSON e apaga a pasta do executável
        """
        import shutil
        games = self._load_db()
        new_games = []
        target_game = None

        for g in games:
            if g['name'] == game_name:
                target_game = g
            else:
                new_games.append(g)

        if target_game:
            # Se for desinstalação total
            if mode == 'full':
                game_dir = os.path.dirname(target_game['path'])
                try:
                    shutil.rmtree(game_dir) # Apaga a pasta toda
                    print(f"Arquivos de {game_name} apagados.")
                    # self._window.evaluate_js(f"window.showNotification('Arquivos de {game_name} apagados.', 'success')")
                except Exception as e:
                    print(f"Erro ao apagar arquivos: {e}")

            # Limpa a capa do cache antes de remover do DB
            self.delete_old_cover(target_game.get('cover'))
            
            # Salva o novo banco sem o jogo
            self._save_db(new_games)
            # self._window.evaluate_js(f"window.showNotification('Jogo removido do Launcher: {game_name}', 'success')")
            return True
        return False

    def _auto_fix_covers(self):
        games = self._load_db()
        updated = False
        
        for g in games:
            current_cover = g.get('cover', '')
            
           
            needs_fix = (current_cover == self.no_cover_path or 
                         not current_cover or 
                         not os.path.exists(current_cover))

            if needs_fix:
                print(f"Buscando capa automática para: {g['name']}")
                searcher = SearchApi(self, g['name'])
                results = searcher.search_steamgrid(g['name'])
                
                if results:
                    # Baixa a nova capa
                    local_path = searcher.download_and_save_cover(results[0])
                    
                    if local_path:
                        # Se já havia um caminho de arquivo que sumiu, limpa por segurança
                        if current_cover and current_cover != self.no_cover_path:
                             self.delete_old_cover(current_cover)
                             
                        g['cover'] = local_path
                        updated = True
                        
                        # Atualiza a interface em tempo real
                        new_base64 = self._get_image_base64(local_path)
                        if self._window:
                            self._window.evaluate_js(
                                f"if(window.updateCardImage) window.updateCardImage('{g['name']}', '{new_base64}')"
                            )
        
        if updated:
            self._save_db(games)
            

    def open_search_window(self, game_name):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        search_html = os.path.join(current_dir, 'gui', 'search.html')
        search_api = SearchApi(self, game_name)
        search_win = webview.create_window(
            f'Buscar Capa: {game_name}', 
            search_html,
            js_api=search_api,
            width=500,
            height=600,
            resizable=False
        )
        
        self.add_window(search_win)
        
    
    def center_initial_window(window):
        """Centraliza a intro (480x360) assim que o app abre."""
        sw, sh = get_screen_resolution()
        x = int((sw - 480) / 2)
        y = int((sh - 360) / 2)
        window.move(x, y)
        
    def finish_intro(self):
        """
        Finaliza a intro e carrega o index.html principal.
        Retorna True para confirmar o recebimento do comando pelo JS.
        """
        try:
            def navigate():
                import time
                # Delay opcional para garantir que a animação seja vista
                #time.sleep(0.1) 
                
                # Configurações da animação
                start_w, start_h = 480, 360
                end_w, end_h = 1200, 800
                steps = 30  # Quantidade de quadros da animação
                delay = 0.01 # Velocidade entre cada passo (segundos) nos testes, sem delay para animação mais fluida

                sw, sh = get_screen_resolution()

                # Loop de animação de redimensionamento
                for i in range(1, steps + 1):
                    
                    current_w = int(start_w + (end_w - start_w) * (i / steps))
                    current_h = int(start_h + (end_h - start_h) * (i / steps))
                    
                   
                    curr_x = int((sw - current_w) / 2)
                    curr_y = int((sh - current_h) / 2)
                    
                   
                    self._window.resize(current_w, current_h)
                    self._window.move(curr_x, curr_y)
                    #time.sleep(delay)
                
                current_dir = os.path.dirname(os.path.abspath(__file__))
                launcher_path = os.path.join(current_dir, 'gui', 'index.html')
                
                # Converte para URL absoluta
                launcher_url = f'file:///{launcher_path.replace("\\", "/")}'
                
                if self._window:
                    self._window.load_url(launcher_url)
                    print("Navegação para o Launcher concluída.")

            # Dispara a navegação em background para não travar o callback do JS
            threading.Thread(target=navigate, daemon=True).start()
            
            
            return True
        except Exception as e:
            print(f"Erro ao iniciar transição: {e}")
            return False

if __name__ == '__main__':
    current_dir = os.path.dirname(os.path.abspath(__file__))
    api = Api()
    
    
    window = webview.create_window(
        'Hunter Launcher', 
        os.path.join(current_dir, 'gui', 'splash.html'), 
        js_api=api,
        width=480,
        height=360,
        frameless=True,          
        background_color='#000000'
    )
   
    api.set_window(window)
    webview.start(center_initial_window, window)