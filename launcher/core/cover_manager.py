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
import webview

class CoverManager:
    def change_cover_local(self, game_name):
        """Abre seletor de arquivos para trocar capa por uma imagem local."""
        if not game_name:
            return None

        # O formato correto para o webview: "Descrição (*.ext1;*.ext2)"
        file_types = ('Imagens (*.jpg;*.png;*.jpeg;*.webp)',) 
        
        try:
            # self._window vem da classe Api que herdará esta
            result = self._window.create_file_dialog(
                webview.FileDialog.OPEN, 
                allow_multiple=False, 
                file_types=file_types
            )
            
            if result:
                new_path = result[0].replace('\\', '/')
                games = self._load_db()
                for g in games:
                    if g['name'] == game_name:
                        g['cover'] = new_path
                self._save_db(games)
                return self._get_image_base64(new_path)
        except Exception as e:
            print(f"Erro ao trocar capa local: {e}")
            
        return None
    
   
    def delete_old_cover(self, path):
        """Remove o arquivo físico da capa antiga se não for a padrão."""
        import os
        try:
            # Verifica se o arquivo existe e se não é a 'no_cover.png'
            if path and os.path.exists(path) and "no_cover.png" not in path:
                os.remove(path)
                print(f"Arquivo antigo removido: {path}")
        except Exception as e:
            print(f"Erro ao deletar arquivo: {e}")

    def update_game_cover(self, game_name, new_path):
        """Atualiza o banco e gerencia a limpeza do arquivo anterior."""
        print(f"Atualizando capa de '{game_name}' para '{new_path}'")
        games = self._load_db()
        for g in games:
            if g['name'] == game_name:
                old_path = g.get('cover')
                # Só deleta se o caminho for realmente diferente
                if old_path and old_path != new_path:
                    self.delete_old_cover(old_path)
                g['cover'] = new_path
                break
        self._save_db(games)
        
        