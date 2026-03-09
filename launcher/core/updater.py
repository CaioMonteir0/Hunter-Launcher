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
import sys
import subprocess
import requests
from pathlib import Path

class Updater:
    def __init__(self, parent_api):
        self.parent = parent_api
        self.repo_url = "https://api.github.com/repos/CaioMonteir0/Hunter-Launcher/releases/latest"
        self.app_data = os.path.join(os.getenv('APPDATA'), 'HunterLauncher')
        
    
    def check_latest_version(self):
         # não consome quota
        url = "https://github.com/CaioMonteir0/Hunter-Launcher/releases/latest"
        try:
            # HEAD apenas pega o cabeçalho, sem baixar nada
            response = requests.head(url, allow_redirects=True, timeout=5)
            # Retorna a tag, ex: 'v1.0.5'
            return response.url.split('/')[-1]
        except:
            return None
        
    def get_download_url(self):
        """
        Consulta o GitHub e retorna (versão, url_download) da última release.
        Retorna (None, None) em caso de erro ou se não encontrar o .exe.
        """
        try:
            
            response = requests.get(self.repo_url, timeout=10)
            response.raise_for_status()
            data = response.json()

            remote_version = data.get("tag_name", "").strip()
            
           
            assets = data.get("assets", [])
            for asset in assets:
                if asset['name'].endswith('.exe'):
                    return remote_version, asset['browser_download_url']
            
            return None, None
            
        except Exception as e:
            print(f"Erro ao buscar informações da release: {e}")
            return None, None

    def run_update(self, download_url):
        exe_path = sys.executable
        ps_script_path = os.path.join(self.app_data, "update_script.ps1")
        
        # Conteúdo do PowerShell com Interface Gráfica (Windows Forms)
        ps_content = f"""
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$form = New-Object System.Windows.Forms.Form
$form.Text = "Hunter Launcher - Atualizando"
$form.Size = New-Object System.Drawing.Size(450, 180)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedDialog"
$form.MaximizeBox = $false
$form.ControlBox = $false

$label = New-Object System.Windows.Forms.Label
$label.Location = New-Object System.Drawing.Point(20, 20)
$label.Size = New-Object System.Drawing.Size(400, 30)
$label.Text = "Preparando atualização..."
$label.Font = New-Object System.Drawing.Font("Segoe UI", 10)
$form.Controls.Add($label)

$progressBar = New-Object System.Windows.Forms.ProgressBar
$progressBar.Location = New-Object System.Drawing.Point(20, 60)
$progressBar.Size = New-Object System.Drawing.Size(390, 25)
$progressBar.Style = "Continuous"
$form.Controls.Add($progressBar)

$form.Show()

$client = New-Object System.Net.WebClient
$url = "{download_url}"
$dest = "{exe_path}.new"
$oldPath = "{exe_path}.old"

$client.Add_DownloadProgressChanged({{
    $progressBar.Value = $_.ProgressPercentage
    $label.Text = "Baixando: " + $_.ProgressPercentage + "%"
}})

$client.Add_DownloadFileCompleted({{
    if ($_.Error) {{
        [System.Windows.Forms.MessageBox]::Show("Erro no download: " + $_.Error.Message)
        $form.Close()
    }} else {{
        $label.Text = "Instalando..."
        
        try {{
            
            if (Test-Path "{exe_path}") {{
                Rename-Item -Path "{exe_path}" -NewName "{os.path.basename(exe_path)}.old" -Force
            }}
            
            
            Move-Item -Path "$dest" -Destination "{exe_path}" -Force
            
            
            $oldPath = "{exe_path}.old"
            $client.Dispose()
            
            # Tenta apagar até 10 vezes com um intervalo de 500ms entre elas
            $tentativa = 0
            
            while ((Test-Path $oldPath) -and ($tentativa -lt 10)) {{
                Start-Sleep -Milliseconds 500
                Remove-Item -Path $oldPath -Force -ErrorAction SilentlyContinue
                $tentativa++
            }}
            
            $label.Text = "Sucesso! Reiniciando..."
            Start-Sleep -s 1
            Start-Process "{exe_path}"
            $form.Close()
        }} catch {{
            [System.Windows.Forms.MessageBox]::Show("Erro na instalação: " + $_.Exception.Message)
            $form.Close()
        }}
    }}
}})

$client.DownloadFileAsync([System.Uri]$url, $dest)
[System.Windows.Forms.Application]::Run($form)
"""
        
        # Salva o script
        with open(ps_script_path, "w", encoding="utf-8-sig") as f:
            f.write(ps_content)

        # Executa o PowerShell de forma independente e fecha o Python
        subprocess.Popen([
            "powershell.exe", 
            "-NoProfile", 
            "-WindowStyle", "Hidden",
            "-ExecutionPolicy", "Bypass", 
            "-File", ps_script_path
        ], creationflags=subprocess.CREATE_NO_WINDOW)
        
        os._exit(0)