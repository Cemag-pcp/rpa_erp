import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel


BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "web" / "templates"
STATIC_DIR = BASE_DIR / "web" / "static"
LOG_FILE = BASE_DIR / "execucao_erp.log"
PIDS_DIR = BASE_DIR / "bot_pids"
PIDS_DIR.mkdir(exist_ok=True)


class BotInfo(BaseModel):
    name: str
    command: List[str]
    running: bool
    last_start: Optional[datetime] = None
    last_stop: Optional[datetime] = None


class BotProcess:
    """
    Representa um bot controlado pela plataforma.
    Mantém apenas informações em memória.
    """

    def __init__(self, name: str, command: List[str]):
        self.name = name
        self.command = command
        self.process: Optional[subprocess.Popen] = None
        self.last_start: Optional[datetime] = None
        self.last_stop: Optional[datetime] = None

    @property
    def running(self) -> bool:
        return self.process is not None and self.process.poll() is None

    @property
    def pid_file(self) -> Path:
        return PIDS_DIR / f"{self.name}.pid"

    def start(self) -> None:
        if self.running:
            return

        cwd = BASE_DIR
        env = os.environ.copy()
        env.setdefault("BOT_NAME", self.name)
        env["BOT_PID_FILE"] = str(self.pid_file)

        self.process = subprocess.Popen(self.command, cwd=str(cwd), env=env)
        self.last_start = datetime.now()

    def stop(self) -> None:
        if not self.running:
            return

        assert self.process is not None
        pid = self.process.pid

        # Primeiro tenta terminar o processo Python "com gentileza"
        self.process.terminate()
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()

        # Em Windows, garante que filhos (incluindo chromedriver/Chrome desse bot) sejam encerrados
        if os.name == "nt" and pid is not None:
            try:
                subprocess.run(
                    ["taskkill", "/PID", str(pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
            except Exception:
                pass

            # Se o bot registrou o PID do chromedriver, mata somente essa árvore
            if self.pid_file.exists():
                try:
                    with self.pid_file.open("r", encoding="utf-8") as f:
                        driver_pid_str = f.read().strip()
                    if driver_pid_str:
                        subprocess.run(
                            ["taskkill", "/PID", driver_pid_str, "/T", "/F"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            check=False,
                        )
                except Exception:
                    pass
                try:
                    self.pid_file.unlink(missing_ok=True)
                except Exception:
                    pass

        self.last_stop = datetime.now()
        self.process = None

    def to_info(self) -> BotInfo:
        return BotInfo(
            name=self.name,
            command=self.command,
            running=self.running,
            last_start=self.last_start,
            last_stop=self.last_stop,
        )


class LogsResponse(BaseModel):
    lines: List[str]


_BOTS: Dict[str, BotProcess] = {
    "requisitar_item": BotProcess(
        name="requisitar_item",
        command=[sys.executable, "-m", "requisitarItem.main"],
    ),
    "transferir_item": BotProcess(
        name="transferir_item",
        command=[sys.executable, "-m", "transferirItem.main"],
    ),
}

def get_bot_or_404(name: str) -> BotProcess:
    bot = _BOTS.get(name)
    if not bot:
        raise HTTPException(status_code=404, detail=f"Bot '{name}' não encontrado.")
    return bot


app = FastAPI(title="Gerenciador de Bots ERP", version="1.0.0")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/api/bots", response_model=List[BotInfo])
def list_bots():
    return [bot.to_info() for bot in _BOTS.values()]


@app.get("/api/bots/{name}", response_model=BotInfo)
def get_bot(name: str):
    bot = get_bot_or_404(name)
    return bot.to_info()


@app.post("/api/bots/{name}/start", response_model=BotInfo)
def start_bot(name: str):
    bot = get_bot_or_404(name)
    if bot.running:
        raise HTTPException(status_code=400, detail="Bot já está em execução.")
    bot.start()
    return bot.to_info()


@app.post("/api/bots/{name}/stop", response_model=BotInfo)
def stop_bot(name: str):
    bot = get_bot_or_404(name)
    if not bot.running:
        raise HTTPException(status_code=400, detail="Bot já está parado.")
    bot.stop()
    return bot.to_info()


def _read_last_log_lines(limit: int = 100) -> List[str]:
    if not LOG_FILE.exists():
        return []

    try:
        with LOG_FILE.open("r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except OSError:
        return []

    return [line.rstrip("\n") for line in lines[-limit:]]


@app.get("/api/logs", response_model=LogsResponse)
def get_logs(limit: int = 100):
    """
    Retorna as últimas `limit` linhas do arquivo de log principal.
    """
    if limit <= 0:
        raise HTTPException(status_code=400, detail="Limit deve ser maior que zero.")

    lines = _read_last_log_lines(limit=limit)
    return LogsResponse(lines=lines)


@app.get("/api/bots/{name}/logs", response_model=LogsResponse)
def get_bot_logs(name: str, limit: int = 100):
    """
    Retorna as últimas `limit` linhas de log associadas ao bot.
    No momento, todos os bots compartilham o mesmo arquivo de log principal.
    """
    _ = get_bot_or_404(name)

    if limit <= 0:
        raise HTTPException(status_code=400, detail="Limit deve ser maior que zero.")

    lines = _read_last_log_lines(limit=limit)
    return LogsResponse(lines=lines)


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("core.bot_manager:app", host="0.0.0.0", port=8000, reload=False)

