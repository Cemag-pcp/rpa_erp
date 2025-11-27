import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from core.db import (
    get_db_connection,
    get_schedule_table_name,
    get_erp_credentials_table_name,
    get_active_schema,
)


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
    schedule_interval_minutes: Optional[int] = None
    headless_mode: Optional[bool] = None
    last_start: Optional[datetime] = None
    last_stop: Optional[datetime] = None
    erp_username: Optional[str] = None
    erp_password: Optional[str] = None


class BotProcess:
    """
    Representa um bot controlado pela plataforma.
    Mantém apenas informações em memória.
    """

    def __init__(self, name: str, command: List[str]):
        self.name = name
        self.command = command
        self.process: Optional[subprocess.Popen] = None
        self.schedule_interval_minutes: Optional[int] = None
        self.headless_mode: Optional[bool] = None
        self.last_start: Optional[datetime] = None
        self.last_stop: Optional[datetime] = None
        self._was_running: bool = False

    @property
    def running(self) -> bool:
        """
        Indica se o processo ainda está em execução.
        Se detectar que o processo finalizou, registra o horário em last_stop
        e limpa a referência para evitar reacessos a um processo morto.
        """
        if self.process is None:
            self._was_running = False
            return False

        alive = self.process.poll() is None

        if alive:
            self._was_running = True
            return True

        # Processo terminou desde a última verificação
        if self._was_running:
            self.last_stop = datetime.now()

        self.process = None
        self._was_running = False
        return False

    @property
    def pid_file(self) -> Path:
        return PIDS_DIR / f"{self.name}.pid"

    def start(self) -> None:
        # Se já estiver rodando, não faz nada
        if self.running:
            return

        # Limpa marcação de execução anterior
        self._was_running = False

        cwd = BASE_DIR
        env = os.environ.copy()
        env.setdefault("BOT_NAME", self.name)
        env["BOT_PID_FILE"] = str(self.pid_file)

        self.process = subprocess.Popen(self.command, cwd=str(cwd), env=env)
        self.last_start = datetime.now()
        # Marca que houve uma execução ativa, para que o próximo acesso a
        # .running possa registrar corretamente o horário de término em last_stop.
        self._was_running = True

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
            schedule_interval_minutes=self.schedule_interval_minutes,
            last_start=self.last_start,
            last_stop=self.last_stop,
        )


class LogsResponse(BaseModel):
    lines: List[str]


class ScheduleUpdate(BaseModel):
    interval_minutes: Optional[int] = None
    headless_mode: Optional[bool] = None


class ErpCredentials(BaseModel):
    username: str
    password: str


def _get_db_connection():
    # Wrapper para manter compatibilidade com o restante do arquivo
    return get_db_connection()


def _qualified(table_name: str) -> str:
    """
    Retorna o nome da tabela qualificado com o schema, se configurado.
    Ex.: bots_rpa_test.rpa_bot_schedule
    """
    schema = get_active_schema()
    if schema:
        return f"{schema}.{table_name}"
    return table_name


def _init_schedule_table() -> None:
    """
    Garante que a tabela de agendamento exista.
    Não levanta erro se o banco estiver indisponível: apenas ignora persistência.
    """
    try:
        conn = _get_db_connection()
    except Exception:
        return

    try:
        with conn:
            with conn.cursor() as cur:
                table_name = _qualified(get_schedule_table_name())
                cur.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        bot_name TEXT PRIMARY KEY,
                        interval_minutes INTEGER,
                        headless_mode BOOLEAN DEFAULT FALSE,
                        updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
    finally:
        conn.close()


def _load_schedules_from_db() -> None:
    """
    Carrega intervalos de agendamento salvos no banco e aplica sobre _BOTS.
    """
    try:
        conn = _get_db_connection()
    except Exception:
        return

    try:
        with conn:
            with conn.cursor() as cur:
                table_name = _qualified(get_schedule_table_name())
                # Garante que a coluna headless_mode exista (migração leve)
                cur.execute(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS headless_mode BOOLEAN DEFAULT FALSE")
                cur.execute(f"SELECT bot_name, interval_minutes, headless_mode FROM {table_name}")
                for bot_name, interval_minutes, headless_mode in cur.fetchall():
                    bot = _BOTS.get(bot_name)
                    if bot is not None:
                        bot.schedule_interval_minutes = interval_minutes
                        bot.headless_mode = headless_mode
    finally:
        conn.close()


def _persist_schedule_to_db(bot: BotProcess) -> None:
    """
    Salva o agendamento de um bot no banco (upsert).
    """
    try:
        conn = _get_db_connection()
    except Exception:
        return

    try:
        with conn:
            with conn.cursor() as cur:
                table_name = _qualified(get_schedule_table_name())
                cur.execute(
                    f"""
                    INSERT INTO {table_name} (bot_name, interval_minutes, headless_mode, updated_at)
                    VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (bot_name)
                    DO UPDATE SET interval_minutes = EXCLUDED.interval_minutes,
                                  headless_mode = EXCLUDED.headless_mode,
                                  updated_at = EXCLUDED.updated_at
                    """,
                    (bot.name, bot.schedule_interval_minutes, bot.headless_mode),
                )
    finally:
        conn.close()


def _init_erp_credentials_table() -> None:
    """
    Garante que a tabela de credenciais ERP exista.
    """
    try:
        conn = _get_db_connection()
    except Exception:
        return

    try:
        with conn:
            with conn.cursor() as cur:
                table_name = _qualified(get_erp_credentials_table_name())
                cur.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        bot_name TEXT PRIMARY KEY,
                        erp_username TEXT,
                        erp_password TEXT,
                        updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
    finally:
        conn.close()


def _load_erp_credentials() -> Dict[str, Dict[str, Optional[str]]]:
    """
    Carrega credenciais ERP salva de um bot esepecífico.
    Retorna dict: { bot_name: {erp_username, erp_password} }.
    """
    try:
        conn = _get_db_connection()
    except Exception:
        return {}

    result: Dict[str, Dict[str, Optional[str]]] = {}

    try:
        with conn:
            with conn.cursor() as cur:
                table_name = _qualified(get_erp_credentials_table_name())
                cur.execute(
                    f"SELECT bot_name, erp_username, erp_password FROM {table_name}"
                )
                for bot_name, username, password in cur.fetchall():
                    result[bot_name] = {
                        "erp_username": username,
                        "erp_password": password,
                    }
    except Exception:
        # Se der erro (tabela não existe, etc.), só retorna vazio
        pass
    finally:
        conn.close()

    return result

def _load_erp_credentials_bot_specific(name_user_bot: str) -> Dict[str, Dict[str, Optional[str]]]:
    """
    Carrega credenciais ERP salva de um bot esepecífico.
    Retorna dict: { bot_name: {erp_username, erp_password} }.
    """
    try:
        conn = _get_db_connection()
    except Exception:
        return {}

    result: Dict[str, Dict[str, Optional[str]]] = {}

    try:
        with conn:
            with conn.cursor() as cur:
                table_name = _qualified(get_erp_credentials_table_name())
                cur.execute(
                    f"SELECT bot_name, erp_username, erp_password FROM {table_name} WHERE bot_name = %s",
                    (name_user_bot,),
                )
                for bot_name, username, password in cur.fetchall():
                    result[bot_name] = {
                        "erp_username": username,
                        "erp_password": password,
                    }
    except Exception:
        # Se der erro (tabela não existe, etc.), só retorna vazio
        pass
    finally:
        conn.close()

    return result

def _persist_erp_credentials(bot_name: str, creds: ErpCredentials) -> None:
    """
    Salva / atualiza credenciais ERP de um bot.
    """
    try:
        conn = _get_db_connection()
    except Exception:
        return

    try:
        with conn:
            with conn.cursor() as cur:
                table_name = _qualified(get_erp_credentials_table_name())
                cur.execute(
                    f"""
                    INSERT INTO {table_name} (bot_name, erp_username, erp_password, updated_at)
                    VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (bot_name)
                    DO UPDATE SET erp_username = EXCLUDED.erp_username,
                                  erp_password = EXCLUDED.erp_password,
                                  updated_at = EXCLUDED.updated_at
                    """,
                    (bot_name, creds.username, creds.password),
                )
    finally:
        conn.close()


_BOTS: Dict[str, BotProcess] = {
    "requisitar_item": BotProcess(
        name="requisitar_item",
        command=[sys.executable, "-m", "bots.requisitarItem.main"],
    ),
    "transferir_item": BotProcess(
        name="transferir_item",
        command=[sys.executable, "-m", "bots.transferirItem.main"],
    ),
    "bot_test_schedule": BotProcess(
        name="bot_test_schedule",
        command=[sys.executable, "-m", "bots.bot_test.main"],
    ),
    "saldo_ao_vivo": BotProcess(
        name="saldo_ao_vivo",
        command=[sys.executable, "-m", "bots.saldoAoVivo.main"],
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

_init_schedule_table()
_init_erp_credentials_table()
_load_schedules_from_db()
_ERP_CREDS = _load_erp_credentials()


@app.get("/api/bots", response_model=List[BotInfo])
def list_bots():
    bots_info: List[BotInfo] = []
    for bot in _BOTS.values():
        info = bot.to_info()
        creds = _ERP_CREDS.get(bot.name, {})
        info.erp_username = creds.get("erp_username")
        info.erp_password = creds.get("erp_password")
         # headless_mode vem direto do objeto em memória
        info.headless_mode = bot.headless_mode
        bots_info.append(info)
    return bots_info


@app.get("/api/bots/{name}", response_model=BotInfo)
def get_bot(name: str):
    bot = get_bot_or_404(name)
    info = bot.to_info()
    creds = _ERP_CREDS.get(bot.name, {})
    info.erp_username = creds.get("erp_username")
    info.erp_password = creds.get("erp_password")
    info.headless_mode = bot.headless_mode
    return info


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


@app.post("/api/bots/{name}/schedule", response_model=BotInfo)
def update_schedule(name: str, body: ScheduleUpdate):
    bot = get_bot_or_404(name)

    if body.interval_minutes is not None and body.interval_minutes <= 0:
        raise HTTPException(status_code=400, detail="interval_minutes deve ser maior que zero ou nulo.")

    bot.schedule_interval_minutes = body.interval_minutes
    bot.headless_mode = body.headless_mode
    _persist_schedule_to_db(bot)
    info = bot.to_info()
    info.headless_mode = bot.headless_mode
    return info


@app.post("/api/bots/{name}/erp_credentials", response_model=BotInfo)
def update_erp_credentials(name: str, body: ErpCredentials):
    bot = get_bot_or_404(name)

    _persist_erp_credentials(bot.name, body)
    # Recarrega credenciais em cache
    _ERP_CREDS[bot.name] = {
        "erp_username": body.username,
        "erp_password": body.password,
    }

    info = bot.to_info()
    info.erp_username = body.username
    info.erp_password = body.password
    return info


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


def _scheduler_loop() -> None:
    import time as _time

    while True:
        now = datetime.now()
        for bot in _BOTS.values():
            interval = bot.schedule_interval_minutes
            if interval is None:
                continue

            # Não dispara se já estiver rodando
            if bot.running:
                continue

            # Contagem do intervalo a partir do FIM da execução
            last_run_end = bot.last_stop

            # Nunca foi executado: inicia imediatamente
            if bot.last_start is None and last_run_end is None:
                should_start = True
            # Já foi executado e já passou o intervalo desde o fim
            elif last_run_end is not None and now - last_run_end >= timedelta(minutes=interval):
                should_start = True
            else:
                should_start = False

            if should_start:
                try:
                    bot.start()
                except Exception:
                    # Em caso de erro, apenas segue; logs de erro podem ser adicionados depois
                    pass

        _time.sleep(60)


# Inicia o scheduler em uma thread separada
import threading as _threading

_scheduler_thread = _threading.Thread(target=_scheduler_loop, daemon=True)
_scheduler_thread.start()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("core.bot_manager:app", host="0.0.0.0", port=8000, reload=False)
