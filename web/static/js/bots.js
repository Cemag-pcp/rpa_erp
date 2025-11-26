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

            tr.innerHTML = `
                <td>${bot.name}</td>
                <td class="${statusClass}">${statusText}</td>
                <td>${bot.last_start ? new Date(bot.last_start).toLocaleString() : "-"}</td>
                <td>${bot.last_stop ? new Date(bot.last_stop).toLocaleString() : "-"}</td>
                <td>
                    <button class="button button--primary" data-action="start" data-name="${bot.name}">Iniciar</button>
                    <button class="button button--danger" data-action="stop" data-name="${bot.name}">Parar</button>
                    <button class="button button--secondary" data-action="logs" data-name="${bot.name}">Ver logs</button>
                </td>
            `;

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
    }
});

document.addEventListener("DOMContentLoaded", () => {
    const refreshButton = document.getElementById("refresh-button");
    if (refreshButton) {
        refreshButton.addEventListener("click", () => loadBots());
    }

    loadBots();
    setInterval(loadBots, 5000);

    const refreshLogsButton = document.getElementById("refresh-logs-button");
    if (refreshLogsButton) {
        refreshLogsButton.addEventListener("click", () => {
            if (currentLogsBot) {
                loadLogs(currentLogsBot);
            }
        });
    }
});
