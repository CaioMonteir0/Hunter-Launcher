/*
 * Hunter-Launcher
 * Copyright (C) 2026 Caio Monteiro
 *
 * Este programa é um software livre: você pode redistribuí-lo e/ou modificá-lo 
 * sob os termos da Licença Pública Geral GNU (GPL), conforme publicada pela 
 * Free Software Foundation, versão 3 da licença, ou (a seu critério) qualquer 
 * versão posterior.
 *
 * Este programa é distribuído na esperança de que seja útil, mas SEM QUALQUER 
 * GARANTIA; sem mesmo a garantia implícita de COMERCIALIZAÇÃO ou ADEQUAÇÃO A 
 * UM PROPÓSITO ESPECÍFICO. Veja a Licença Pública Geral GNU para mais detalhes.
 *
 * Você deve ter recebido uma cópia da Licença Pública Geral GNU junto com 
 * este programa. Se não, veja: https://www.gnu.org/licenses/
 *
 * Projeto disponível em: https://github.com/CaioMonteir0/Hunter-Launcher
 */



/**
 * Variáveis de controle para o Menu de Capa
 */
let selectedGameForMenu = null;

/** Variáveis de controle para a Biblioteca */
let rawLibrary = [];

/** Variável global para rastrear o filtro atual*/
let currentSortMode = "az";

/** Variável global para capturar o alias caso tenha*/
let maybeAlias = "";

let updateAvailable = false; // Variável para controlar o estado da atualização
let versionAvailable = ""; // Variável para armazenar a versão disponível

async function handleAction(action, data = null, gameName = null) {
  if (!window.pywebview || !window.pywebview.api) {
    console.error("API do Python não detectada.");
    return;
  }

  const loader = document.getElementById("loader");

  switch (action) {
    case "ADD_GAME":
      loader.classList.remove("hidden");
      try {
        const newGame = await window.pywebview.api.add_game();
        if (newGame) {
          const games = await window.pywebview.api.get_library();
          rawLibrary = games || [];

          applyFilters();
        }
      } catch (err) {
        console.error("Erro ao adicionar jogo:", err);
        window.showNotification("Erro ao adicionar jogo", "error");
      } finally {
        loader.classList.add("hidden");
      }
      break;

    case "PLAY":
      const success = await window.pywebview.api.launch_game(data);
      if (success) {
        window.showNotification("Iniciando " + gameName + "...", "success");
      } else {
        window.showNotification("Falha ao iniciar jogo", "error");
      }
      break;

    case "CHANGE_COVER_LOCAL":
      const localCover = await window.pywebview.api.change_cover_local(data);
      const gameTitle = maybeAlias !== "" ? maybeAlias : data;
      if (localCover) {
        refreshGameCover(data, localCover);
        window.showNotification(
          "Capa de " + gameTitle + " atualizada!",
          "success",
        );
      }
      break;

    case "OPEN_SEARCH_WINDOW":
      window.pywebview.api.open_search_window(data);
      break;

    case "LOAD_LIBRARY":
      const games = await window.pywebview.api.get_library();
      rawLibrary = games || [];
      applyFilters();
      break;

    default:
      console.warn(`Ação "${action}" não reconhecida.`);
  }
}

// Função chamada pelo botão de 3 pontos no card do jogo
window.showOptionsMenu = function (event, gameName, gameAlias) {
  event.preventDefault();
  event.stopPropagation();

  maybeAlias = gameAlias;
  selectedGameForMenu = gameName;
  const menu = document.getElementById("options-menu");

  menu.classList.remove("hidden", "go-left");

  const menuWidth = menu.offsetWidth;
  const menuHeight = menu.offsetHeight;
  const windowWidth = window.innerWidth;
  const windowHeight = window.innerHeight;

  const padding = 10;

  const submenuWidth = 50;

  let posX = event.clientX + padding;

  if (posX + menuWidth + submenuWidth > windowWidth) {
    posX = event.clientX - menuWidth + 5;
    menu.classList.add("go-left");
  } else {
    posX = event.clientX - 5;
    menu.classList.remove("go-left");
  }

  let posY = event.clientY;

  if (posY + menuHeight > windowHeight) {
    posY = windowHeight - menuHeight - padding;
  }

  if (posY < 0) posY = padding;

  menu.style.position = "fixed";
  menu.style.top = `${posY}px`;
  menu.style.left = `${posX}px`;

  const closeMenu = (e) => {
    if (!menu.contains(e.target)) {
      menu.classList.add("hidden");
      document.removeEventListener("click", closeMenu);
    }
  };
  setTimeout(() => document.addEventListener("click", closeMenu), 50);
};

window.handleCoverChoice = function (type) {
  if (type === "online") {
    const gameTitle = maybeAlias !== "" ? maybeAlias : selectedGameForMenu;

    window.pywebview.api.open_search_window(selectedGameForMenu, gameTitle);
  } else {
    window.handleAction("CHANGE_COVER_LOCAL", selectedGameForMenu);
  }
  document.getElementById("options-menu").classList.add("hidden");
};

window.removeGame = function (mode) {
  const isFull = mode === "full";
  const fullTrashIcon = `
                  <svg width="18px" height="18px" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path d="M10 12L14 16M14 12L10 16M4 6H20M16 6L15.7294 5.18807C15.4671 4.40125 15.3359 4.00784 15.0927 3.71698C14.8779 3.46013 14.6021 3.26132 14.2905 3.13878C13.9376 3 13.523 3 12.6936 3H11.3064C10.477 3 10.0624 3 9.70951 3.13878C9.39792 3.26132 9.12208 3.46013 8.90729 3.71698C8.66405 4.00784 8.53292 4.40125 8.27064 5.18807L8 6M18 6V16.2C18 17.8802 18 18.7202 17.673 19.362C17.3854 19.9265 16.9265 20.3854 16.362 20.673C15.7202 21 14.8802 21 13.2 21H10.8C9.11984 21 8.27976 21 7.63803 20.673C7.07354 20.3854 6.6146 19.9265 6.32698 19.362C6 18.7202 6 17.8802 6 16.2V6" stroke="#E53E3E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path> </g></svg>

  `;
  const launcherTrashIcon = `
                  <svg width="18px" height="18px" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path d="M11 15L9 13M9 13L11 11M9 13H12C12.9319 13 13.3978 13 13.7654 13.1522C14.2554 13.3552 14.6448 13.7446 14.8478 14.2346C15 14.6022 15 15.0681 15 16M18 6L17.1991 18.0129C17.129 19.065 17.0939 19.5911 16.8667 19.99C16.6666 20.3412 16.3648 20.6235 16.0011 20.7998C15.588 21 15.0607 21 14.0062 21H9.99377C8.93927 21 8.41202 21 7.99889 20.7998C7.63517 20.6235 7.33339 20.3412 7.13332 19.99C6.90607 19.5911 6.871 19.065 6.80086 18.0129L6 6M4 6H20M16 6L15.7294 5.18807C15.4671 4.40125 15.3359 4.00784 15.0927 3.71698C14.8779 3.46013 14.6021 3.26132 14.2905 3.13878C13.9376 3 13.523 3 12.6936 3H11.3064C10.477 3 10.0624 3 9.70951 3.13878C9.39792 3.26132 9.12208 3.46013 8.90729 3.71698C8.66405 4.00784 8.53292 4.40125 8.27064 5.18807L8 6" stroke="#F7A400" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path> </g></svg>

  `;

  const gameTitle = maybeAlias !== "" ? maybeAlias : selectedGameForMenu;

  window.showConfirmModal({
    title: isFull ? "Desinstalar Jogo" : "Remover do Launcher",
    message: isFull
      ? `Isso apagará permanentemente todos os arquivos de "${gameTitle}" do seu disco. Esta ação não pode ser desfeita.`
      : `Deseja remover "${gameTitle}" da sua biblioteca? Os arquivos do jogo permanecerão intactos.`,

    confirmText: isFull ? "Apagar Tudo" : "Remover",
    confirmClass: isFull
      ? "bg-red-600 hover:bg-red-500"
      : "bg-slate-600 hover:bg-slate-500",
    validate: () => false,
    onConfirm: async () => {
      const success = await window.pywebview.api.delete_game_request(
        selectedGameForMenu,
        mode,
      );
      if (success) {
        window.handleAction("LOAD_LIBRARY");
        window.showNotification(
          isFull
            ? gameTitle + " foi desinstalado!"
            : gameTitle + " foi removido do launcher!",
          "success",
        );
      } else {
        window.showNotification(
          isFull
            ? "Falha ao tentar desinstalar " + gameTitle
            : "Falha ao tentar remover " + gameTitle,
          "error",
        );
      }
    },
  });

  document.getElementById("confirm-icon").innerHTML = isFull
    ? fullTrashIcon
    : launcherTrashIcon;
};

/**
 * Renderiza um card individual na tela
 */
function addGameToUI(game) {
  const container = document.getElementById("game-library");
  const isListMode = container.classList.contains("flex-col");
  const displayName =
    game.alias && game.alias.trim() !== "" ? game.alias : game.name;

  const cardHtml = `
        <div class="game-card group relative overflow-hidden rounded-xl bg-slate-800/50 border border-slate-700/50 ${isListMode ? "list-mode" : ""}" data-game-name="${game.name}" ondblclick="handleAction('PLAY', '${game.path.replace(/\\/g, "/")}', '${displayName}')">
            <div class="aspect-[2/3] w-full overflow-hidden">
                <img src="${game.cover}" alt="${displayName}" class="game-card-img h-full w-full object-cover">
            </div>

            <div class="card-gradient absolute inset-0 flex ${isListMode ? "flex-row items-center justify-between" : "flex-col justify-end"} p-4 transition-all ${isListMode ? "" : "group-hover:pb-6"}">
            <div class="card-info flex flex-col ${isListMode ? "min-w-0" : "mb-2"}">
                <span class="text-xs font-semibold text-blue-400 uppercase tracking-wider">${game.size}</span>
                <h3 title="${displayName}" class="font-bold text-sm leading-tight truncate">${displayName}</h3>
            </div>

                <div class="flex gap-24 items-center opacity-0 group-hover:opacity-100 transition-opacity duration-300" >
    <button title="Jogar" onclick="handleAction('PLAY', '${game.path.replace(/\\/g, "/")}', '${displayName}')" 
            class="text-slate-400 hover:text-blue-500 transition-colors duration-200 outline-none">
        <svg width="16px" height="16px" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M20.4086 9.35258C22.5305 10.5065 22.5305 13.4935 20.4086 14.6474L7.59662 21.6145C5.53435 22.736 3 21.2763 3 18.9671L3 5.0329C3 2.72368 5.53435 1.26402 7.59661 2.38548L20.4086 9.35258Z" 
                  fill="currentColor"></path>
        </svg>
    </button>

    <button onclick="showOptionsMenu(event, '${game.name}', '${game.alias || ""}')" 
            class="text-slate-400 hover:text-white transition-colors duration-200 outline-none ml-4" title="Opções">
        <svg width="16px" height="16px" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
            <path d="M12.15 28.012v-0.85c0.019-0.069 0.050-0.131 0.063-0.2 0.275-1.788 1.762-3.2 3.506-3.319 1.95-0.137 3.6 0.975 4.137 2.787 0.069 0.238 0.119 0.488 0.181 0.731v0.85c-0.019 0.056-0.050 0.106-0.056 0.169-0.269 1.65-1.456 2.906-3.081 3.262-0.125 0.025-0.25 0.063-0.375 0.094h-0.85c-0.056-0.019-0.113-0.050-0.169-0.056-1.625-0.262-2.862-1.419-3.237-3.025-0.037-0.156-0.081-0.3-0.119-0.444zM20.038 3.988l-0 0.85c-0.019 0.069-0.050 0.131-0.056 0.2-0.281 1.8-1.775 3.206-3.538 3.319-1.944 0.125-3.588-1-4.119-2.819-0.069-0.231-0.119-0.469-0.175-0.7v-0.85c0.019-0.056 0.050-0.106 0.063-0.162 0.3-1.625 1.244-2.688 2.819-3.194 0.206-0.069 0.425-0.106 0.637-0.162h0.85c0.056 0.019 0.113 0.050 0.169 0.056 1.631 0.269 2.863 1.419 3.238 3.025 0.038 0.15 0.075 0.294 0.113 0.437zM20.037 15.575v0.85c-0.019 0.069-0.050 0.131-0.063 0.2-0.281 1.794-1.831 3.238-3.581 3.313-1.969 0.087-3.637-1.1-4.106-2.931-0.050-0.194-0.094-0.387-0.137-0.581v-0.85c0.019-0.069 0.050-0.131 0.063-0.2 0.275-1.794 1.831-3.238 3.581-3.319 1.969-0.094 3.637 1.1 4.106 2.931 0.050 0.2 0.094 0.394 0.137 0.588z" 
                  fill="currentColor"></path>
        </svg>
    </button>
</div>
            </div>
        </div>
    `;

  container.insertAdjacentHTML("beforeend", cardHtml);
}

function toggleViewMode() {
  const container = document.getElementById("game-library");
  const cards = document.querySelectorAll(".game-card");

  container.classList.toggle("grid-view");
  container.classList.toggle("list-view");

  cards.forEach((card) => card.classList.toggle("list-mode"));
}

function refreshGameCover(gameName, newUrl) {
  const cardImg = document.querySelector(`[data-game-name="${gameName}"] img`);
  if (cardImg) cardImg.src = newUrl;
}

function renderFullLibrary(games) {
  const container = document.getElementById("game-library");
  container.innerHTML = "";
  if (games && games.length > 0) games.forEach((game) => addGameToUI(game));
}

window.addEventListener("pywebviewready", () => {
  const toggleBtn = document.getElementById("grid-view");

  if (toggleBtn) {
    toggleBtn.disabled = true;
    toggleBtn.style.opacity = "0.5";
    toggleBtn.style.cursor = "not-allowed";

    setTimeout(() => {
      toggleBtn.disabled = false;
      toggleBtn.style.opacity = "1";
      toggleBtn.style.cursor = "pointer";
    }, 5000);
  }
  setTimeout(() => handleAction("LOAD_LIBRARY"), 100);
});

window.toggleSettings = async function () {
  const modal = document.getElementById("settings-modal");
  const isOpening = modal.classList.contains("hidden");

  if (isOpening) {
    renderUpdateState();
    // Antes de mostrar, busca o que está salvo no Python
    const settings = await window.pywebview.api.get_settings();
    document.getElementById("api-key-input").value =
      settings.steamgrid_key || "";
    modal.classList.remove("hidden");

    // busca a versão do App
    window.pywebview.api.get_app_version().then((version) => {
      const versionElement = document.getElementById("app-version-display");
      if (versionElement) {
        versionElement.innerText = version;
      }
    });
  } else {
    modal.classList.add("hidden");
  }
};

window.saveApiSettings = async function () {
  const key = document.getElementById("api-key-input").value.trim();
  const btn = document.getElementById("btn-save-settings");
  const saveBtn = event.target;
  
  const arrow = document.getElementById("arrow-path");
  arrow.classList.add("animate-arrow");
  btn.classList.add("is-saving");
  saveBtn.disabled = true;

  const success = await window.pywebview.api.save_api_settings({
    steamgrid_key: key,
  });

  if (success) {
    // Feedback visual de sucesso
    window.showNotification("SteamGridDB Key salva!", "success");
    setTimeout(() => {
      
      arrow.classList.remove("animate-arrow");
      btn.classList.remove("is-saving");
      saveBtn.disabled = false;
      window.toggleSettings();
    }, 1000);
  } else {
    arrow.classList.remove("animate-arrow");
    btn.classList.remove("is-saving");
    window.showNotification(
      "Erro ao salvar as configurações no AppData.",
      "error",
    );
   
    saveBtn.disabled = false;
  }
  
};

window.showNotification = function (message, type = "info", soundName = null) {
  const container = document.getElementById("notification-container");
  const toast = document.createElement("div");
  

  if (soundName) {
    const audioFiles = {
      update: "sound/updater-sound.mp3"
    };

    const soundPath = audioFiles[soundName];
    if (soundPath) {
      const audio = new Audio(soundPath);
      audio.volume = 1.0;
      audio.play().catch((e) => console.error("Erro ao tocar áudio:", e));
    }
  }

  const colors = {
    success: "border-green-500 text-green-400",
    error: "border-red-500 text-red-400",
    warning: "border-yellow-500 text-yellow-400",
    info: "border-blue-500 text-blue-400",
  };

  // CORREÇÃO: Os SVGs agora são strings
  const icon =
    type === "success"
      ? '<svg width="16px" height="16px" viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg" fill="#000000"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"><path fill="#00942c" d="M512 64a448 448 0 1 1 0 896 448 448 0 0 1 0-896zm-55.808 536.384-99.52-99.584a38.4 38.4 0 1 0-54.336 54.336l126.72 126.72a38.272 38.272 0 0 0 54.336 0l262.4-262.464a38.4 38.4 0 1 0-54.272-54.336L456.192 600.384z"></path></g></svg>'
      : type === "error"
        ? '<svg width="16px" height="16px" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"><path fill-rule="evenodd" clip-rule="evenodd" d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10zm-1.5-5.009c0-.867.659-1.491 1.491-1.491.85 0 1.509.624 1.509 1.491 0 .867-.659 1.509-1.509 1.509-.832 0-1.491-.642-1.491-1.509zM11.172 6a.5.5 0 0 0-.499.522l.306 7a.5.5 0 0 0 .5.478h1.043a.5.5 0 0 0 .5-.478l.305-7a.5.5 0 0 0-.5-.522h-1.655z" fill="#b80000"></path></g></svg>'
        : '<svg height="16px" width="16px" version="1.1" id="Capa_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 432.464 432.464" xml:space="preserve" fill="#000000"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <g> <path style="fill:#666666;" d="M417.297,363.067L232.809,43.523c-2.895-5.015-7.057-8.561-11.743-10.66v-2.277l-12.349,0.055 c-8.138,0.52-16.064,4.813-20.723,12.882L3.505,363.067c-9.959,17.249,2.49,38.811,22.407,38.811H394.89 C414.808,401.878,427.256,380.316,417.297,363.067z"></path> <path style="fill:#808080;" d="M15.166,363.067L199.655,43.523c9.959-17.249,34.856-17.249,44.815,0l184.489,319.544 c9.959,17.249-2.49,38.811-22.407,38.811H37.574C17.656,401.878,5.207,380.316,15.166,363.067z"></path> <polygon style="fill:#F9ED82;" points="48.184,369.878 222.062,68.712 395.939,369.878 "></polygon> <circle style="fill:#666666;" cx="222.062" cy="323.818" r="24"></circle> <path style="fill:#666666;" d="M222.062,148.818L222.062,148.818c-12.982,0-23.251,10.992-22.367,23.944l6.348,93.091 c0.574,8.424,7.576,14.965,16.02,14.965h0c8.444,0,15.445-6.54,16.02-14.965l6.348-93.091 C245.312,159.811,235.044,148.818,222.062,148.818z"></path> </g> </g></svg>';

  toast.className = `bg-slate-900 border-l-4 ${colors[type]} p-4 rounded-lg shadow-2xl min-w-[300px] transform translate-x-full transition-all duration-300 flex items-center justify-between group`;

  toast.innerHTML = `
        <div class="flex items-center gap-3">
            <span class="text-lg">${icon}</span>
            <p class="text-sm font-medium text-slate-200">${message}</p>
        </div>
        <button class="text-slate-500 hover:text-white ml-4">&times;</button>
    `;

  container.appendChild(toast);

  // Animação de entrada (delay pequeno para o navegador processar o elemento)
  setTimeout(() => toast.classList.remove("translate-x-full"), 100);

  // Auto-remover após 4 segundos
  const closeTimer = setTimeout(() => removeToast(toast), 4000);

  // Botão fechar manual
  toast.querySelector("button").onclick = () => {
    clearTimeout(closeTimer);
    removeToast(toast);
  };
};

window.removeToast = function (toast) {
  toast.classList.add("translate-x-full", "opacity-0");
  setTimeout(() => toast.remove(), 300);
};

window.updateCardImage = function (gameName, base64Data) {
  const cards = document.querySelectorAll(".game-card");
  cards.forEach((card) => {
    if (card.querySelector("h3").innerText.trim() === gameName) {
      const img = card.querySelector("img");
      if (img) img.src = base64Data;
    }
  });

  const game = rawLibrary.find((g) => g.name === gameName);
  if (game) {
    game.cover = base64Data;
  }
};

/**
 * Abre o modal de confirmação genérico
 * @param {Object} config - { title, message, icon, confirmText, confirmClass, onConfirm }
 */
window.showConfirmModal = function (config) {
  const modal = document.getElementById("confirm-modal");
  const title = document.getElementById("confirm-title");
  const message = document.getElementById("confirm-message");
  const icon = document.getElementById("confirm-icon");
  const input = document.getElementById("confirm-input");
  const btnExecute = document.getElementById("confirm-button-execute");

  title.innerText = config.title || "Confirmação";
  message.innerText = config.message || "Deseja continuar?";
  icon.innerText = config.icon || "⚠️";
  btnExecute.innerText = config.confirmText || "Confirmar";

  btnExecute.className = `flex-1 py-3 rounded-lg font-bold transition-all transform active:scale-95 text-white ${config.confirmClass || "bg-red-600 hover:bg-red-500"}`;

  if (config.showInput) {
    input.classList.remove("hidden");
    input.value = config.inputValue || "";
    input.placeholder = config.inputPlaceholder || "";

    if (config.validate) {
      const checkValidation = () => {
        const isValid = config.validate(input.value);
        btnExecute.disabled = !isValid;

        btnExecute.style.opacity = isValid ? "1" : "0.5";
        btnExecute.style.cursor = isValid ? "pointer" : "not-allowed";
      };

      input.oninput = checkValidation;
      checkValidation();
    } else {
      btnExecute.disabled = false;
      btnExecute.style.opacity = "1";
    }

    setTimeout(() => input.focus(), 100);
  } else {
    input.classList.add("hidden");
    btnExecute.disabled = false;
    btnExecute.style.opacity = "1";
  }

  btnExecute.onclick = async () => {
    if (btnExecute.disabled) return;

    const value = config.showInput ? input.value : null;
    await config.onConfirm(value);
    window.closeConfirmModal();
  };

  modal.classList.remove("hidden");
};

window.closeConfirmModal = function () {
  document.getElementById("confirm-modal").classList.add("hidden");
};

window.renameGame = function () {
  const currentName = selectedGameForMenu; // Nome original do jogo

  window.showConfirmModal({
    title: "Mudar nome do jogo",
    message: `Como você quer chamar "${maybeAlias !== "" ? maybeAlias : currentName}" na sua biblioteca?`,
    confirmText: "Salvar Nome",
    confirmClass: "bg-blue-600 hover:bg-blue-500",
    showInput: true,
    inputPlaceholder: "Digite o novo nome...",
    validate: (value) => value.trim().length > 0,
    onConfirm: async (newAlias) => {
      if (newAlias !== null) {
        const success = await window.pywebview.api.rename_game_alias(
          currentName,
          newAlias,
        );
        if (success) {
          window.showNotification("Alterado para: " + newAlias, "success");
          window.handleAction("LOAD_LIBRARY"); // Recarrega a UI
        } else {
          window.showNotification("Falha ao mudar o nome do jogo", "error");
        }
      }
    },
  });
  const svgCode = `
  <svg width="18px" height="18px" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path opacity="0.15" d="M8 16H12L18 10L14 6L8 12V16Z" fill="#ffffff"></path> <path d="M14 6L8 12V16H12L18 10M14 6L17 3L21 7L18 10M14 6L18 10M10 4L4 4L4 20L20 20V14" stroke="#ffffff" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"></path> </g></svg>
  `;
  document.getElementById("confirm-icon").innerHTML = svgCode;
  document.getElementById("options-menu").classList.add("hidden");
};

let filterTimeout;

function applyFilters() {
  clearTimeout(filterTimeout);

  filterTimeout = setTimeout(() => {
    let filtered = [...rawLibrary];
    const searchTerm = document
      .getElementById("search-input")
      .value.toLowerCase();
    const sortVal = currentSortMode;

    if (searchTerm) {
      filtered = filtered.filter((g) => {
        const name = (g.alias || g.name).toLowerCase();
        return name.includes(searchTerm);
      });
    }

    const parseToMB = (sizeStr) => {
      if (!sizeStr) return 0;

      const size = parseFloat(sizeStr.replace(",", ".")) || 0;
      const unit = sizeStr.toUpperCase();

      if (unit.includes("GB")) {
        return size * 1024; // Converte GB para MB
      }
      if (unit.includes("TB")) {
        return size * 1024 * 1024; // Converte TB para MB
      }

      return size;
    };

    filtered.sort((a, b) => {
      const nameA = (a.alias || a.name).toLowerCase();
      const nameB = (b.alias || b.name).toLowerCase();

      if (sortVal === "az") return nameA.localeCompare(nameB);
      if (sortVal === "za") return nameB.localeCompare(nameA);

      if (sortVal === "size-desc") return parseToMB(b.size) - parseToMB(a.size);
      if (sortVal === "size-asc") return parseToMB(a.size) - parseToMB(b.size);
    });

    renderFullLibrary(filtered);
  }, 100);
}

document.getElementById("search-wrapper").onclick = function () {
  this.classList.add("active");
  document.getElementById("search-input").focus();
};

document.getElementById("search-input").onblur = function () {
  if (this.value === "") {
    document.getElementById("search-wrapper").classList.remove("active");
  }
};

document.getElementById("search-input").onkeypress = function (e) {
  if (e.key === "Enter") applyFilters();
};

function toggleSortMenu(event) {
  event.stopPropagation();
  const menu = document.getElementById("sort-menu");
  menu.classList.toggle("hidden");
}

function selectSort(mode, label) {
  currentSortMode = mode;

  document.getElementById("sort-selected-label").innerText = label;

  document.getElementById("sort-menu").classList.add("hidden");

  applyFilters();
}

document.addEventListener("click", (e) => {
  const menu = document.getElementById("sort-menu");
  const container = document.getElementById("sort-dropdown-container");
  if (!container.contains(e.target)) {
    menu.classList.add("hidden");
  }
});

// ícone de maximizar/restaurar
let isMaximized = false;

function toggleMaxIcon() {
  window.pywebview.api.toggle_maximize();

  // Inverte o estado visual
  isMaximized = !isMaximized;
  const container = document.getElementById("max-icon-container");
  const btn = document.getElementById("max-btn");

  if (isMaximized) {
    // Ícone de Restaurar (Duas janelinhas sobrepostas)
    btn.title = "Restaurar";
    container.innerHTML = `
            <svg width="18px" height="18px" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path d="M5.08496 4C5.29088 3.4174 5.8465 3 6.49961 3H9.99961C11.6565 3 12.9996 4.34315 12.9996 6V9.5C12.9996 10.1531 12.5822 10.7087 11.9996 10.9146V6C11.9996 4.89543 11.1042 4 9.99961 4H5.08496Z" fill="#ffffff"></path> <path d="M4.5 5H9.5C10.3284 5 11 5.67157 11 6.5V11.5C11 12.3284 10.3284 13 9.5 13H4.5C3.67157 13 3 12.3284 3 11.5V6.5C3 5.67157 3.67157 5 4.5 5ZM4.5 6C4.22386 6 4 6.22386 4 6.5V11.5C4 11.7761 4.22386 12 4.5 12H9.5C9.77614 12 10 11.7761 10 11.5V6.5C10 6.22386 9.77614 6 9.5 6H4.5Z" fill="#ffffff"></path> </g></svg>
        `;
  } else {
    // Ícone de Maximizar (Quadrado único)
    btn.title = "Maximizar";
    container.innerHTML = `
            <svg width="12" height="12" viewBox="0 0 12 12">
                <rect width="9" height="9" x="1.5" y="1.5" fill="none" stroke="currentColor" stroke-width="1"/>
            </svg>
        `;
  }
}

// Abas do menu de configurações
window.switchTab = function (tabName) {
  const apiTab = document.getElementById("tab-api");
  const updateTab = document.getElementById("tab-updates");
  const aboutTab = document.getElementById("tab-about");
  const apiContent = document.getElementById("content-api");
  const updateContent = document.getElementById("content-updates");
  const aboutContent = document.getElementById("content-about");
  const btnSave = document.getElementById("btn-save-settings");
  const actionsSpace = document.getElementById("actions-space");

  if (tabName === "updates") {
    renderUpdateState();
  }

  switch (tabName) {
    case "api":
      // --- ABA API ATIVA ---
      apiTab.classList.add("border-blue-500", "text-blue-400");
      apiTab.classList.remove("border-transparent", "text-slate-400");

      // --- ABA UPDATES INATIVA ---
      updateTab.classList.remove("border-blue-500", "text-blue-400");
      updateTab.classList.add("border-transparent", "text-slate-400");

      // --- ABA ABOUT INATIVA ---
      aboutTab.classList.remove("border-blue-500", "text-blue-400");
      aboutTab.classList.add("border-transparent", "text-slate-400");

      // Visibilidade
      updateContent.classList.add("hidden");
      aboutContent.classList.add("hidden");
      apiContent.classList.remove("hidden");
      btnSave.classList.remove("hidden");
      actionsSpace.classList.remove("hidden");
      

      break;
    case "updates":
      renderUpdateState();

      // --- ABA API INATIVA ---
      apiTab.classList.remove("border-blue-500", "text-blue-400");
      apiTab.classList.add("border-transparent", "text-slate-400");

      // --- ABA UPDATES ATIVA ---
      updateTab.classList.add("border-blue-500", "text-blue-400");
      updateTab.classList.remove("border-transparent", "text-slate-400");

      // --- ABA ABOUT INATIVA ---
      aboutTab.classList.remove("border-blue-500", "text-blue-400");
      aboutTab.classList.add("border-transparent", "text-slate-400");

      // Visibilidade
      apiContent.classList.add("hidden");
      aboutContent.classList.add("hidden");
      updateContent.classList.remove("hidden");
      btnSave.classList.add("hidden");
      actionsSpace.classList.add("hidden");
      

      break;
    case "about":

      // --- ABA ABOUT ATIVA ---
      aboutTab.classList.add("border-blue-500", "text-blue-400");
      aboutTab.classList.remove("border-transparent", "text-slate-400");

      // --- ABA API INATIVA ---
      apiTab.classList.remove("border-blue-500", "text-blue-400");
      apiTab.classList.add("border-transparent", "text-slate-400");

      // --- ABA UPDATES INATIVA ---
      updateTab.classList.remove("border-blue-500", "text-blue-400");
      updateTab.classList.add("border-transparent", "text-slate-400");

      // Visibilidade
      apiContent.classList.add("hidden");
      updateContent.classList.add("hidden");
      aboutContent.classList.remove("hidden");
      actionsSpace.classList.add("hidden");
      

      break;
  }
};

window.checkUpdatesManual = function () {
  const btn = document.getElementById("btn-check-updates");
  const icon = document.getElementById("update-icon");
  const statusText = document.getElementById("update-status-text");

  if (!icon || btn.disabled) return;

  icon.classList.add("animate-spin-active");
  btn.disabled = true;
  statusText.innerText = "Verificando atualizações...";
  statusText.classList.replace("text-green-400", "text-slate-500");

  window.pywebview.api.check_manual_update().then((result) => {
    setTimeout(() => {
      icon.classList.remove("animate-spin-active");
      btn.disabled = false;

      if (result && result.available) {
        updateAvailable = true;
        versionAvailable = result.version;

        renderUpdateState();
      } else {
        updateAvailable = false;
        statusText.innerText = "O Launcher já está na versão mais recente.";
      }
    }, 3000);
  });
};

window.addEventListener("pywebviewready", function () {
  window.pywebview.api
    .check_updates_on_start()
    .then((result) => {
      if (result && result.available) {
        updateAvailable = result.available;
        versionAvailable = result.version;

        renderUpdateState();
      }
    })
    .catch((err) => {
      console.error("[JS] Erro ao verificar atualizações:", err);
    });
});

function renderUpdateState() {
  const btn = document.getElementById("btn-check-updates");
  const statusText = document.getElementById("update-status-text");

  if (updateAvailable) {
    statusText.innerText = `Versão ${versionAvailable} disponível!`;
    statusText.classList.remove("text-slate-500");
    statusText.classList.add("text-green-400");

    btn.innerHTML = "<span>Instalar Agora</span>";

    btn.onclick = () => window.pywebview.api.start_launcher_update();
  } else {
    // Estado padrão (Caso não haja update)
    statusText.innerText = "O Launcher está na versão mais recente.";
    statusText.classList.add("text-slate-500");
    statusText.classList.remove("text-green-400");

    btn.innerHTML = "<span>Procurar Atualizações</span>";

    btn.onclick = () => window.checkUpdatesManual();
  }
}
