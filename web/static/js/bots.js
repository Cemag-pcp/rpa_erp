async function loadBots() {
    const tbody = document.getElementById("bots-body");
    if (!tbody) return;

    try {
        const resp = await fetch("/api/bots");
        if (!resp.ok) {
            throw new Error("Falha ao buscar bots");
        }

        const bots = await resp.json();
        tbody.innerHTML = "";

        bots.forEach((bot) => {
            const tr = document.createElement("tr");

            const statusClass = bot.running ? "status-running" : "status-stopped";
            const statusText = bot.running ? "Executando" : "Parado";

            const interval = bot.schedule_interval_minutes;
            const scheduleLabel = interval
                ? `A cada ${interval} min`
                : "Desligado";
            const isScheduled = interval != null;

            const erpUser = bot.erp_username || "";
            const headless = bot.headless_mode === true;

            tr.innerHTML = `
                <td>${bot.name}</td>
                <td class="${statusClass}">${statusText}</td>
                <td>
                    <select class="schedule-select" data-name="${bot.name}">
                        <option value="">Desligado</option>
                        <option value="2">A cada 2 min</option>
                        <option value="30">A cada 30 min</option>
                        <option value="60">A cada 60 min</option>
                        <option value="120">A cada 120 min</option>
                    </select>
                    <span class="schedule-label">${scheduleLabel}</span>
                </td>
                <td>
                    <input type="checkbox" class="headless-checkbox" data-name="${bot.name}" ${headless ? "checked" : ""} />
                </td>
                <td>
                    <span class="erp-label">${erpUser || "Nǜo configurado"}</span>
                    <button class="button button--secondary" data-action="config-erp" data-name="${bot.name}">Configurar</button>
                </td>
                <td>${bot.last_start ? new Date(bot.last_start).toLocaleString() : "-"}</td>
                <td>${bot.last_stop ? new Date(bot.last_stop).toLocaleString() : "-"}</td>
                <td>
                    <button class="button button--primary" data-action="start" data-name="${bot.name}" ${isScheduled ? "disabled" : ""}>Iniciar</button>
                    <button class="button button--danger" data-action="stop" data-name="${bot.name}">Parar</button>
                    <button class="button button--secondary" data-action="logs" data-name="${bot.name}">Ver logs</button>
                </td>
            `;

            const select = tr.querySelector(".schedule-select");
            if (select) {
                select.value = interval ? String(interval) : "";
            }

            tbody.appendChild(tr);
        });
    } catch (e) {
        alert("Erro ao carregar lista de bots.");
        console.error(e);
    }
}

let currentLogsBot = null;

async function loadLogs(botName) {
    const container = document.getElementById("logs-container");
    if (!container || !botName) return;

    currentLogsBot = botName;

    try {
        const resp = await fetch(`/api/bots/${encodeURIComponent(botName)}/logs?limit=100`);
        if (!resp.ok) {
            throw new Error("Falha ao buscar logs");
        }

        const data = await resp.json();
        const lines = Array.isArray(data.lines) ? data.lines : [];
        container.textContent = lines.join("\n");
    } catch (e) {
        console.error(e);
        container.textContent = "Erro ao carregar logs.";
    }
}

async function startBot(name) {
    try {
        const resp = await fetch(`/api/bots/${name}/start`, { method: "POST" });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            alert("Erro ao iniciar: " + (err.detail || resp.status));
        }
    } catch (e) {
        alert("Erro de comunicação com o servidor.");
        console.error(e);
    } finally {
        await loadBots();
    }
}

async function stopBot(name) {
    try {
        const resp = await fetch(`/api/bots/${name}/stop`, { method: "POST" });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            alert("Erro ao parar: " + (err.detail || resp.status));
        }
    } catch (e) {
        alert("Erro de comunicação com o servidor.");
        console.error(e);
    } finally {
        await loadBots();
    }
}

document.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;

    const action = target.getAttribute("data-action");
    const name = target.getAttribute("data-name");

    if (!action || !name) return;

    if (action === "start") {
        startBot(name);
    } else if (action === "stop") {
        stopBot(name);
    } else if (action === "logs") {
        loadLogs(name);
    } else if (action === "config-erp") {
        openErpConfig(name);
    }
});

document.addEventListener("change", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;

    const isSchedule = target.classList.contains("schedule-select");
    const isHeadless = target.classList.contains("headless-checkbox");

    if (!isSchedule && !isHeadless) return;

    const botName = target.getAttribute("data-name");
    if (!botName) return;

    // Encontra a linha para ler ambos os valores
    const row = target.closest("tr");
    if (!row) return;

    const scheduleSelect = row.querySelector(".schedule-select");
    const headlessCheckbox = row.querySelector(".headless-checkbox");

    const value = scheduleSelect ? scheduleSelect.value : "";
    const interval = value ? parseInt(value, 10) : null;
    const headless = headlessCheckbox ? headlessCheckbox.checked : null;

    updateSchedule(botName, interval, headless);
});

document.addEventListener("DOMContentLoaded", () => {
    const refreshButton = document.getElementById("refresh-button");
    if (refreshButton) {
        refreshButton.addEventListener("click", () => loadBots());
    }

    // Carrega a lista de bots ao abrir/atualizar a página
    loadBots();

    const refreshLogsButton = document.getElementById("refresh-logs-button");
        if (refreshLogsButton) {
            refreshLogsButton.addEventListener("click", () => {
                if (currentLogsBot) {
                    loadLogs(currentLogsBot);
                }
            });
        }
});

async function updateSchedule(name, intervalMinutes, headlessMode) {
    try {
        const resp = await fetch(`/api/bots/${encodeURIComponent(name)}/schedule`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ interval_minutes: intervalMinutes, headless_mode: headlessMode })
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            alert("Erro ao atualizar agendamento: " + (err.detail || resp.status));
        } else {
            await loadBots();
        }
    } catch (e) {
        console.error(e);
        alert("Erro de comunicação ao atualizar agendamento.");
    }
}

function openErpConfig(botName) {
    const currentUser = prompt("Login ERP para o bot '" + botName + "':");
    if (currentUser === null) return;

    const currentPass = prompt("Senha ERP para o bot '" + botName + "':");
    if (currentPass === null) return;

    saveErpCredentials(botName, currentUser, currentPass);
}

async function saveErpCredentials(name, username, password) {
    try {
        const resp = await fetch('/api/bots/' + encodeURIComponent(name) + '/erp_credentials', {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            alert('Erro ao salvar credenciais ERP: ' + (err.detail || resp.status));
        } else {
            await loadBots();
        }
    } catch (e) {
        console.error(e);
        alert('Erro de comunicacao ao salvar credenciais ERP.');
    }
}

